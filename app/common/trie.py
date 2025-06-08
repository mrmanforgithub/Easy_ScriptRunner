# coding: utf-8
from queue import Queue

class Trie:
    """ 支持所有字符的 Trie """

    def __init__(self):
        self.key = ''  # 当前节点的完整键
        self.value = None  # 当前节点存储的值
        self.children = {}  # 使用字典存储子节点，支持任意字符
        self.isEnd = False  # 标记当前节点是否是某个键的结尾

    def insert(self, key: str, value):
        """ 插入键值对 """
        key = key.lower()  # 统一转换为小写
        node = self
        for c in key:
            if c not in node.children:  # 如果字符不在子节点中，则创建新节点
                node.children[c] = Trie()
            node = node.children[c]  # 移动到子节点

        node.isEnd = True  # 标记当前节点为键的结尾
        node.key = key  # 存储完整键
        node.value = value  # 存储值

    def get(self, key, default=None):
        """ 获取键对应的值 """
        node = self.searchPrefix(key)
        if not (node and node.isEnd):  # 如果节点不存在或不是键的结尾，则返回默认值
            return default
        return node.value

    def searchPrefix(self, prefix):
        """ 查找匹配前缀的节点 """
        prefix = prefix.lower()  # 统一转换为小写
        node = self
        for c in prefix:
            if c not in node.children:  # 如果字符不在子节点中，则返回 None
                return None
            node = node.children[c]  # 移动到子节点
        return node

    def items(self, prefix):
        """ 查找所有匹配前缀的键值对 """
        node = self.searchPrefix(prefix)
        if not node:  # 如果没有匹配前缀的节点，则返回空列表
            return []

        q = Queue()  # 使用队列进行广度优先搜索
        result = []  # 存储结果
        q.put(node)

        while not q.empty():
            node = q.get()
            if node.isEnd:  # 如果当前节点是某个键的结尾，则将其加入结果
                result.append((node.key, node.value))

            for c in node.children.values():  # 将所有子节点加入队列
                q.put(c)

        return result


    def clear(self):
        """ 清空 Trie 的所有内容 """
        self.key = ''
        self.value = None
        self.children.clear()
        self.isEnd = False