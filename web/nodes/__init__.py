"""Nodos del grafo web."""
from web.nodes.supervisor import supervisor_node
from web.nodes.jibril_node import jibril_node
from web.nodes.shiro_node import shiro_node
from web.nodes.chlammy_node import chlammy_node
from web.nodes.hitl_node import hitl_node

__all__ = ["supervisor_node", "jibril_node", "shiro_node", "chlammy_node", "hitl_node"]
