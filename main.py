# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from database import init_db, get_db
from models import (
    ClienteORM, ProdutoORM, PedidoORM,
    Cliente, ClienteEntrada, Produto, ProdutoEntrada, Pedido, PedidoEntrada,
    PedidoFactory
)
from security import verificar_api_key

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="API IDEA - Loja de Informática", version="2.0", lifespan=lifespan)

@app.get("/")
def raiz():
    return {"mensagem": "API IDEA rodando com SQLAlchemy!"}

# CLIENTES
@app.post("/clientes", response_model=Cliente, status_code=201)
def criar_cliente(dados: ClienteEntrada, db: Session = Depends(get_db)):
    cliente = ClienteORM(**dados.model_dump())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente

@app.get("/clientes", response_model=List[Cliente])
def listar_clientes(db: Session = Depends(get_db)):
    return db.query(ClienteORM).all()

@app.put("/clientes/{id}", response_model=Cliente)
def editar_cliente(id: int, dados: ClienteEntrada, db: Session = Depends(get_db), _=Depends(verificar_api_key)):
    cliente = db.query(ClienteORM).get(id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    cliente.nome = dados.nome
    cliente.cpf = dados.cpf
    cliente.email = dados.email
    cliente.telefone = dados.telefone
    cliente.endereco = dados.endereco

    db.commit()
    db.refresh(cliente)
    return cliente

@app.delete("/clientes/{id}", status_code=204)
def excluir_cliente(id: int, db: Session = Depends(get_db), _=Depends(verificar_api_key)):
    cliente = db.query(ClienteORM).get(id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    db.delete(cliente)
    db.commit()

# PRODUTOS
@app.post("/produtos", response_model=Produto, status_code=201)
def criar_produto(dados: ProdutoEntrada, db: Session = Depends(get_db)):
    produto = ProdutoORM(**dados.model_dump())
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto

@app.get("/produtos", response_model=List[Produto])
def listar_produtos(db: Session = Depends(get_db)):
    return db.query(ProdutoORM).all()

# PEDIDOS
@app.post("/pedidos", response_model=Pedido, status_code=201)
def criar_pedido(dados: PedidoEntrada, db: Session = Depends(get_db)):
    cliente = db.query(ClienteORM).get(dados.cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    produtos = []
    valor_total = 0
    for pid in dados.itens:
        produto = db.query(ProdutoORM).get(pid)
        if not produto or produto.estoque <= 0:
            raise HTTPException(status_code=400, detail=f"Produto {pid} indisponível")
        produtos.append(produto)
        valor_total += float(produto.preco)
        produto.estoque -= 1

    pedido = PedidoFactory.criar(
        cliente_id=dados.cliente_id,
        endereco_entrega=dados.endereco_entrega,
        forma_pagamento=dados.forma_pagamento,
        produtos=produtos,
        valor_total=valor_total
    )
    db.add(pedido)
    db.commit()
    db.refresh(pedido)

    return Pedido(
        id=pedido.id,
        cliente_id=pedido.cliente_id,
        itens=[item.produto_id for item in pedido.itens],
        valor_total=float(pedido.valor_total),
        status=pedido.status
    )

@app.get("/pedidos", response_model=List[Pedido])
def listar_pedidos(db: Session = Depends(get_db)):
    pedidos = db.query(PedidoORM).all()
    return [
        Pedido(
            id=p.id,
            cliente_id=p.cliente_id,
            itens=[item.produto_id for item in p.itens],
            valor_total=float(p.valor_total),
            status=p.status
        )
        for p in pedidos
    ]

# DELETES
@app.delete("/pedidos/{id}", status_code=204)
def deletar_pedido(id: int, db: Session = Depends(get_db), _=Depends(verificar_api_key)):
    pedido = db.query(PedidoORM).get(id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    for item in pedido.itens:
        produto = db.query(ProdutoORM).get(item.produto_id)
        if produto:
            produto.estoque += 1

    db.delete(pedido)
    db.commit()

@app.delete("/pedidos/{id}/item/{produto_id}", response_model=Pedido)
def remover_item_pedido(id: int, produto_id: int, db: Session = Depends(get_db), _=Depends(verificar_api_key)):
    pedido = db.query(PedidoORM).get(id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    item = next((i for i in pedido.itens if i.produto_id == produto_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Produto não está no pedido")

    produto = db.query(ProdutoORM).get(produto_id)
    if produto:
        produto.estoque += 1
        pedido.valor_total = float(pedido.valor_total) - float(item.preco_unitario)

    pedido.itens.remove(item)
    db.delete(item)
    db.commit()
    db.refresh(pedido)

    return Pedido(
        id=pedido.id,
        cliente_id=pedido.cliente_id,
        itens=[i.produto_id for i in pedido.itens],
        valor_total=float(pedido.valor_total),
        status=pedido.status
    )