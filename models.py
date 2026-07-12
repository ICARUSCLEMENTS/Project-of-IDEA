from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import List

from database import Base

class ClienteORM(Base):
    __tablename__ = "Cliente"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)
    cpf = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    telefone = Column(String)
    endereco = Column(String)

    pedidos = relationship("PedidoORM", back_populates="cliente")


class ProdutoORM(Base):
    __tablename__ = "Produto"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)
    sku = Column(String, unique=True, nullable=False)
    descricao = Column(String)
    preco = Column(Numeric(10, 2), nullable=False)
    estoque = Column(Integer, nullable=False)
    categoria = Column(String)
    fabricante = Column(String)


class PedidoORM(Base):
    __tablename__ = "Pedido"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("Cliente.id"), nullable=False)
    endereco_entrega = Column(String, nullable=False)
    forma_pagamento = Column(String, nullable=False)
    valor_total = Column(Numeric(10, 2), nullable=False)
    status = Column(String, nullable=False)

    cliente = relationship("ClienteORM", back_populates="pedidos")
    itens = relationship("PedidoItemORM", back_populates="pedido", cascade="all, delete-orphan")


class PedidoItemORM(Base):
    __tablename__ = "PedidoItem"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("Pedido.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("Produto.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)

    pedido = relationship("PedidoORM", back_populates="itens")
    produto = relationship("ProdutoORM")


# Schemas usados na API

class ClienteEntrada(BaseModel):
    nome: str
    cpf: str
    email: str
    telefone: str
    endereco: str

class Cliente(ClienteEntrada):
    id: int

    class Config:
        from_attributes = True


class ProdutoEntrada(BaseModel):
    nome: str
    sku: str
    descricao: str
    preco: float
    estoque: int
    categoria: str
    fabricante: str

class Produto(ProdutoEntrada):
    id: int

    class Config:
        from_attributes = True


class PedidoEntrada(BaseModel):
    cliente_id: int
    itens: List[int]
    endereco_entrega: str
    forma_pagamento: str

class Pedido(BaseModel):
    id: int
    cliente_id: int
    itens: List[int]
    valor_total: float
    status: str


class PedidoFactory:
    @staticmethod
    def criar(cliente_id: int, endereco_entrega: str, forma_pagamento: str, produtos: list, valor_total: float) -> PedidoORM:
        pedido = PedidoORM(
            cliente_id=cliente_id,
            endereco_entrega=endereco_entrega,
            forma_pagamento=forma_pagamento,
            valor_total=valor_total,
            status="Aguardando pagamento"
        )
        pedido.itens = [
            PedidoItemORM(produto_id=p.id, quantidade=1, preco_unitario=p.preco)
            for p in produtos
        ]
        return pedido