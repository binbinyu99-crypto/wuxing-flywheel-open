"""Engram Accumulator v2 — AI² 认知残差累积引擎

AI¹ = AI does tasks (linear growth)
AI² = AI improves AI (self-catalytic growth)

The Engram system is what makes each flywheel run smarter than the last.
It stores cognitive residuals — the "leftovers" that don't fit into structured 
conclusions but contain valuable pattern information.

v2 升级:
- 语义相似度替代简单字符匹配
- 残差分类与权重衰减
- 跨run认知图谱
- 残差冲突检测
"""

import json
import re
import math
from typing import List, Dict, Optional, Any, Tuple
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class Engram:
    """单个认知残差记录"""
    run_id: str
    topic: str
    content: str
    engram_type: str  # insight, contradiction, gap, pattern, warning
    confidence: float = 0.5
    source_agent: str = ""
    related_concepts: List[str] = field(default_factory=list)
    timestamp: str = ""
    decay_weight: float = 1.0  # 随时间衰减
    
    def to_dict(self) -> dict:
        return {
            'run_id': self.run_id,
            'topic': self.topic,
            'content': self.content,
            'type': self.engram_type,
            'confidence': self.confidence,
            'source': self.source_agent,
            'concepts': self.related_concepts,
            'timestamp': self.timestamp,
            'weight': self.decay_weight
        }


class SemanticMatcher:
    """语义相似度匹配器
    
    使用TF-IDF风格的词频统计 + 概念重叠度来计算相似度。
    不依赖外部向量数据库，纯Python实现。
    """
    
    # 中文停用词
    STOPWORDS = set('的了是在有和与或不也都而且但是因为所以如果那么这个那个一个')
    
    def __init__(self):
        self.idf_cache: Dict[str, float] = {}
        self.doc_count = 0
    
    def tokenize(self, text: str) -> List[str]:
        """简易中英文分词"""
        # 英文词
        english = re.findall(r'[a-zA-Z]{2,}', text.lower())
        # 中文双字词（bigram）
        chinese = re.findall(r'[\u4e00-\u9fff]', text)
        bigrams = [chinese[i] + chinese[i+1] for i in range(len(chinese)-1)]
        # 合并，去停用词
        tokens = english + bigrams
        return [t for t in tokens if t not in self.STOPWORDS and len(t) > 1]
    
    def compute_similarity(self, text_a: str, text_b: str) -> float:
        """计算两段文本的语义相似度 [0, 1]"""
        tokens_a = set(self.tokenize(text_a))
        tokens_b = set(self.tokenize(text_b))
        
        if not tokens_a or not tokens_b:
            return 0.0
        
        # Jaccard similarity
        intersection = tokens_a & tokens_b
        union = tokens_a | tokens_b
        jaccard = len(intersection) / len(union) if union else 0.0
        
        # Concept overlap bonus: longer shared tokens count more
        concept_bonus = sum(len(t) for t in intersection) / max(sum(len(t) for t in union), 1)
        
        # Combined score (weighted)
        return 0.6 * jaccard + 0.4 * concept_bonus
    
    def find_similar(self, query: str, candidates: List[str], top_k: int = 5, threshold: float = 0.15) -> List[Tuple[int, float]]:
        """找到最相似的候选文本
        
        Returns:
            List of (index, similarity_score) sorted by score desc
        """
        scores = []
        for i, candidate in enumerate(candidates):
            sim = self.compute_similarity(query, candidate)
            if sim >= threshold:
                scores.append((i, sim))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class EngramStore:
    """Engram存储与检索
    
    支持两种后端:
    - memory: 内存存储（默认，适合开源版）
    - postgres: PostgreSQL存储（生产版）
    """
    
    def __init__(self, backend: str = 'memory', pg_config: dict = None):
        self.backend = backend
        self.pg_config = pg_config
        self.matcher = SemanticMatcher()
        
        # Memory backend
        self._store: List[Engram] = []
        self._topic_index: Dict[str, List[int]] = defaultdict(list)
    
    def store(self, engram: Engram):
        """存储一个Engram"""
        if self.backend == 'postgres' and self.pg_config:
            self._store_pg(engram)
        else:
            idx = len(self._store)
            self._store.append(engram)
            # Index by topic keywords
            for token in self.matcher.tokenize(engram.topic):
                self._topic_index[token].append(idx)
    
    def retrieve(self, topic: str, top_k: int = 5, min_similarity: float = 0.15) -> List[Engram]:
        """检索与给定主题最相关的Engrams"""
        if self.backend == 'postgres' and self.pg_config:
            return self._retrieve_pg(topic, top_k)
        
        if not self._store:
            return []
        
        # Semantic search
        topics = [e.topic + ' ' + e.content[:200] for e in self._store]
        matches = self.matcher.find_similar(topic, topics, top_k=top_k, threshold=min_similarity)
        
        results = []
        for idx, score in matches:
            engram = self._store[idx]
            # Apply decay weight
            effective_score = score * engram.decay_weight
            if effective_score >= min_similarity:
                results.append(engram)
        
        return results
    
    def extract_from_result(self, run_id: str, topic: str, result: dict) -> List[Engram]:
        """从飞轮run结果中提取Engrams
        
        提取源:
        - 玄武/鲲鹏的残差和数据缺口
        - 白虎的未解决攻击
        - 谛听的证据缺失
        - 青龙的新颖种子
        """
        engrams = []
        
        kunpeng = result.get('kunpeng', {})
        if isinstance(kunpeng, str):
            try: kunpeng = json.loads(kunpeng)
            except: kunpeng = {}
        
        # 1. Data gaps → gap engrams
        data_gaps = kunpeng.get('data_gaps', [])
        if isinstance(data_gaps, list):
            for gap in data_gaps:
                if isinstance(gap, dict):
                    engrams.append(Engram(
                        run_id=run_id,
                        topic=topic,
                        content=gap.get('gap', '') + ' | ' + gap.get('consequence', ''),
                        engram_type='gap',
                        confidence=1.0 - float(gap.get('severity', 0.5)),
                        source_agent='kunpeng',
                        related_concepts=self.matcher.tokenize(gap.get('gap', ''))[:5]
                    ))
        
        # 2. Unresolved attacks → warning engrams
        eo = result.get('element_outputs', {})
        baihu_raw = eo.get('baihu', '')
        if baihu_raw:
            baihu = self._safe_parse(baihu_raw) if isinstance(baihu_raw, str) else baihu_raw
            if isinstance(baihu, dict):
                for atk in baihu.get('attacks', []):
                    if isinstance(atk, dict) and atk.get('unresolved', False):
                        engrams.append(Engram(
                            run_id=run_id,
                            topic=topic,
                            content=str(atk.get('attack', ''))[:500],
                            engram_type='warning',
                            confidence=float(atk.get('severity', 0.5)),
                            source_agent='baihu'
                        ))
                
                # Residuals → pattern engrams
                for res in baihu.get('residuals', []):
                    if isinstance(res, dict):
                        engrams.append(Engram(
                            run_id=run_id,
                            topic=topic,
                            content=str(res.get('description', ''))[:500],
                            engram_type='pattern',
                            source_agent='baihu'
                        ))
        
        # 3. Core contradiction → insight engram
        core_contradiction = kunpeng.get('core_contradiction', '')
        if core_contradiction and len(str(core_contradiction)) > 20:
            engrams.append(Engram(
                run_id=run_id,
                topic=topic,
                content=str(core_contradiction)[:500],
                engram_type='contradiction',
                confidence=0.8,
                source_agent='kunpeng'
            ))
        
        # 4. Dao merge one-sentence → insight engram
        dao = kunpeng.get('dao_merge', {})
        if isinstance(dao, str):
            try: dao = json.loads(dao)
            except: dao = {}
        if isinstance(dao, dict):
            one_sentence = dao.get('one_sentence_dao', '')
            if one_sentence and len(str(one_sentence)) > 20:
                engrams.append(Engram(
                    run_id=run_id,
                    topic=topic,
                    content=str(one_sentence)[:500],
                    engram_type='insight',
                    confidence=0.9,
                    source_agent='xuanwu'
                ))
        
        return engrams
    
    def build_context_prompt(self, topic: str, max_engrams: int = 5) -> str:
        """为新run构建Engram上下文注入prompt
        
        Returns:
            A string to prepend to the first round's user prompt,
            providing relevant historical cognitive residuals.
        """
        relevant = self.retrieve(topic, top_k=max_engrams)
        if not relevant:
            return ""
        
        lines = ["[历史认知残差 — 以下是之前分析中积累的相关认知，供本次分析参考]\n"]
        
        for i, eng in enumerate(relevant, 1):
            type_labels = {
                'insight': '💡 洞察',
                'contradiction': '⚠️ 矛盾',
                'gap': '❓ 缺口',
                'pattern': '🔍 模式',
                'warning': '🔴 警告'
            }
            label = type_labels.get(eng.engram_type, eng.engram_type)
            lines.append(f"{i}. [{label}] (来自 {eng.run_id}): {eng.content[:300]}")
        
        lines.append("\n[请在分析中考虑以上历史认知。如果新证据推翻了旧认知，请明确标注。]\n")
        
        return '\n'.join(lines)
    
    def detect_conflicts(self, new_engrams: List[Engram]) -> List[Dict]:
        """检测新Engram与已有Engram的冲突
        
        当两个insight/contradiction类型的engram在相似主题上给出矛盾结论时触发。
        """
        conflicts = []
        
        for new_eng in new_engrams:
            if new_eng.engram_type not in ('insight', 'contradiction'):
                continue
            
            similar = self.retrieve(new_eng.topic, top_k=3, min_similarity=0.3)
            for old_eng in similar:
                if old_eng.run_id == new_eng.run_id:
                    continue
                if old_eng.engram_type not in ('insight', 'contradiction'):
                    continue
                
                # Simple conflict detection: high topic similarity but different content
                topic_sim = self.matcher.compute_similarity(new_eng.topic, old_eng.topic)
                content_sim = self.matcher.compute_similarity(new_eng.content, old_eng.content)
                
                if topic_sim > 0.4 and content_sim < 0.3:
                    conflicts.append({
                        'new_run': new_eng.run_id,
                        'old_run': old_eng.run_id,
                        'topic_similarity': round(topic_sim, 3),
                        'content_similarity': round(content_sim, 3),
                        'new_content': new_eng.content[:200],
                        'old_content': old_eng.content[:200],
                        'note': 'Similar topic, divergent conclusions — cognitive evolution or error?'
                    })
        
        return conflicts
    
    def apply_decay(self, decay_rate: float = 0.95):
        """对所有Engram应用时间衰减"""
        for eng in self._store:
            eng.decay_weight *= decay_rate
    
    def stats(self) -> Dict:
        """返回Engram存储统计"""
        type_counts = defaultdict(int)
        for eng in self._store:
            type_counts[eng.engram_type] += 1
        
        return {
            'total': len(self._store),
            'by_type': dict(type_counts),
            'unique_topics': len(set(e.topic for e in self._store)),
            'unique_runs': len(set(e.run_id for e in self._store))
        }
    
    def _store_pg(self, engram: Engram):
        """PostgreSQL存储后端"""
        try:
            import psycopg2
            conn = psycopg2.connect(**self.pg_config)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO engrams (run_id, topic, content, engram_type, confidence, 
                                     source_agent, related_concepts, decay_weight)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (engram.run_id, engram.topic, engram.content, engram.engram_type,
                  engram.confidence, engram.source_agent, 
                  json.dumps(engram.related_concepts), engram.decay_weight))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[engram] PG store error: {e}")
            # Fallback to memory
            self._store.append(engram)
    
    def _retrieve_pg(self, topic: str, top_k: int = 5) -> List[Engram]:
        """PostgreSQL检索后端 — 使用trigram相似度"""
        try:
            import psycopg2
            conn = psycopg2.connect(**self.pg_config)
            cur = conn.cursor()
            # Use LIKE for basic matching (pg_trgm would be better with extension)
            keywords = self.matcher.tokenize(topic)[:3]
            if not keywords:
                conn.close()
                return []
            
            conditions = ' OR '.join([f"topic ILIKE '%{kw}%' OR content ILIKE '%{kw}%'" for kw in keywords])
            cur.execute(f"""
                SELECT run_id, topic, content, engram_type, confidence, source_agent, decay_weight
                FROM engrams 
                WHERE {conditions}
                ORDER BY confidence * decay_weight DESC
                LIMIT %s
            """, (top_k,))
            
            results = []
            for row in cur.fetchall():
                results.append(Engram(
                    run_id=row[0], topic=row[1], content=row[2],
                    engram_type=row[3], confidence=row[4],
                    source_agent=row[5], decay_weight=row[6]
                ))
            conn.close()
            return results
        except Exception as e:
            print(f"[engram] PG retrieve error: {e}")
            return []
    
    def _safe_parse(self, text):
        if not text or not isinstance(text, str):
            return None
        text = text.strip()
        idx = text.find('{')
        if idx >= 0:
            text = text[idx:]
        try:
            return json.loads(text)
        except:
            try:
                return json.loads(text, strict=False)
            except:
                return None
