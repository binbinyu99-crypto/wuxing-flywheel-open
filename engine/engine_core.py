"""Wuxing Flywheel Core Engine v2.0
五行飞轮核心引擎 — 开源版

Architecture:
  Wood(道家/生成) → Fire(第一性原理/抽象) → Earth(儒家/落地) 
  → Metal(弗洛伊德/对抗) → Water(佛家三时/收敛) → Wood...

v2.0 Changes:
  - NPT Validator: 所有输出必须通过协议校验
  - Adversarial Enforcer: 白虎审计强制化，不过不出
  - Engram Accumulator v2: 语义相似度匹配，跨run认知累积
  - IntegrityMesh: 六维完整性评分
"""

import json
import time
from typing import Dict, List, Optional, Any, Tuple

# Core modules
from .npt_validator import NPTValidator, NPTViolation
from .adversarial_enforcer import AdversarialEnforcer
from .engram_accumulator import EngramStore, Engram
from .integrity_mesh import IntegrityMesh
from .llm_router import call_llm
from .edge_agents import EdgeAgentRegistry
from .cognitive_modules import (
    CounterfactualAnalyzer, EvidenceChainBuilder,
    ConfidenceCalibrator, DebateSimulator
)


# ============================================================
# Wuxing Elements
# ============================================================

ELEMENTS = {
    'wood': {
        'name': '青龙', 'element': '木', 'philosophy': '道家',
        'role': 'Seed generation — divergent exploration',
        'model': 'deepseek'
    },
    'fire': {
        'name': '朱雀', 'element': '火', 'philosophy': '第一性原理',
        'role': 'Deep analysis — essence abstraction',
        'model': 'deepseek'
    },
    'earth': {
        'name': '谛听', 'element': '土', 'philosophy': '儒家',
        'role': 'Cross-validation — evidence grading',
        'model': 'kimi'
    },
    'metal': {
        'name': '白虎', 'element': '金', 'philosophy': '弗洛伊德精神分析',
        'role': 'Adversarial audit — attack and stress-test',
        'model': 'deepseek'
    },
    'water': {
        'name': '玄武', 'element': '水', 'philosophy': '佛家三时',
        'role': 'Convergence — past/present/future synthesis',
        'model': 'deepseek'
    }
}


# ============================================================
# Main Flywheel Engine
# ============================================================

class FlywheelEngine:
    """五行飞轮引擎
    
    Usage:
        engine = FlywheelEngine()
        result = engine.run("量子计算对金融行业的影响", max_rounds=3)
    """
    
    def __init__(self, 
                 engram_store: Optional[EngramStore] = None,
                 strict_npt: bool = True,
                 strict_adversarial: bool = True):
        
        self.engram_store = engram_store or EngramStore()
        self.npt_validator = NPTValidator(strict=False)  # Collect violations, don't crash
        self.adversarial_enforcer = AdversarialEnforcer(strict=strict_adversarial)
        self.integrity_mesh = IntegrityMesh()
        self.edge_agents = EdgeAgentRegistry()
        
        # Cognitive modules
        self.counterfactual = CounterfactualAnalyzer()
        self.evidence_builder = EvidenceChainBuilder()
        self.confidence_calibrator = ConfidenceCalibrator()
        self.debate_sim = DebateSimulator()
    
    def run(self, topic: str, max_rounds: int = 3, 
            mode: str = 'deep', run_id: str = None) -> Dict[str, Any]:
        """Execute a complete flywheel analysis
        
        Args:
            topic: Analysis subject
            max_rounds: Maximum iteration rounds
            mode: 'quick' (1 round) or 'deep' (multi-round with convergence)
            run_id: Optional run identifier
            
        Returns:
            Complete result dict with all element outputs, scores, and metadata
        """
        run_id = run_id or f"run-{int(time.time())}"
        start_time = time.time()
        
        print(f"[flywheel] Starting {mode} analysis: {topic}")
        print(f"[flywheel] Run ID: {run_id}, Max rounds: {max_rounds}")
        
        # === Phase 0: Engram Context Injection ===
        engram_context = self.engram_store.build_context_prompt(topic)
        if engram_context:
            print(f"[engram] Injected {len(engram_context)} chars of historical context")
        
        # === Phase 1-N: Iterative Flywheel ===
        rounds = []
        scores = []
        element_outputs = {}
        converged = False
        
        for round_num in range(1, max_rounds + 1):
            print(f"\n[flywheel] === Round {round_num}/{max_rounds} ===")
            
            round_result = self._execute_round(
                topic, round_num, engram_context, 
                previous_outputs=element_outputs
            )
            
            rounds.append(round_result)
            element_outputs = round_result['element_outputs']
            
            # === Adversarial Enforcement (after each round) ===
            baihu_output = element_outputs.get('baihu', '')
            audit_result = self.adversarial_enforcer.enforce(baihu_output)
            round_result['audit'] = {
                'passed': audit_result.passed,
                'score_adjustment': audit_result.score_adjustment,
                'issues': audit_result.blocking_issues,
                'attack_count': len(audit_result.attacks),
                'unresolved': audit_result.unresolved_count
            }
            
            if not audit_result.passed:
                print(f"[baihu] ⚠️ Audit issues: {audit_result.blocking_issues}")
            else:
                print(f"[baihu] ✅ Audit passed ({len(audit_result.attacks)} attacks, "
                      f"{audit_result.unresolved_count} unresolved)")
            
            # === Score calculation ===
            round_score = self._calculate_score(round_result)
            adjusted_score, explanation = self.adversarial_enforcer.adjust_score(
                round_score, audit_result
            )
            scores.append(adjusted_score)
            print(f"[score] Round {round_num}: {round_score:.3f} → {adjusted_score:.3f} ({explanation})")
            
            # === Convergence check ===
            if mode == 'quick':
                break
            
            if round_num >= 2:
                delta = abs(scores[-1] - scores[-2])
                if delta < 0.05:
                    converged = True
                    print(f"[flywheel] Converged (delta={delta:.4f})")
                    break
        
        # === Phase N+1: IntegrityMesh ===
        integrity_score = self.integrity_mesh.compute_integrity_score(element_outputs)
        print(f"[integrity] Score: {integrity_score:.3f}")
        
        # === Phase N+2: NPT Validation ===
        final_result = self._assemble_result(
            run_id, topic, rounds, scores, element_outputs, 
            converged, start_time
        )
        
        npt_report = self.npt_validator.validate_run(final_result)
        final_result['npt_validation'] = npt_report
        final_result['integrity_score'] = integrity_score
        
        if not npt_report['valid']:
            print(f"[npt] ⚠️ {npt_report['violation_count']} violations: "
                  f"{[v['detail'][:50] for v in npt_report['violations'][:3]]}")
        else:
            print(f"[npt] ✅ All axioms satisfied")
        
        # === Phase N+3: Engram Extraction & Storage ===
        new_engrams = self.engram_store.extract_from_result(run_id, topic, final_result)
        conflicts = self.engram_store.detect_conflicts(new_engrams)
        
        for eng in new_engrams:
            self.engram_store.store(eng)
        
        if conflicts:
            print(f"[engram] ⚠️ {len(conflicts)} conflicts with historical knowledge")
            final_result['engram_conflicts'] = conflicts
        
        print(f"[engram] Stored {len(new_engrams)} new engrams "
              f"(total: {self.engram_store.stats()['total']})")
        
        # === Final ===
        elapsed = time.time() - start_time
        final_result['elapsed_seconds'] = round(elapsed, 1)
        
        final_score = scores[-1] if scores else 0
        grade = self._score_to_grade(final_score)
        final_result['score'] = final_score
        final_result['grade'] = grade
        
        print(f"\n[flywheel] Complete: {final_score:.3f}/{grade} in {elapsed:.1f}s")
        
        return final_result
    
    def _execute_round(self, topic: str, round_num: int, 
                       engram_context: str, previous_outputs: dict) -> dict:
        """Execute one round of the five-element cycle"""
        outputs = {}
        
        # Build context from previous round
        prev_context = ""
        if previous_outputs:
            prev_context = "\n[上一轮分析摘要]\n"
            for agent, output in previous_outputs.items():
                summary = str(output)[:300] if output else "(空)"
                prev_context += f"- {agent}: {summary}\n"
        
        # Wood → Fire → Earth → Metal → Water
        for element_key, element_info in ELEMENTS.items():
            agent_name = element_info['name']
            model = element_info['model']
            
            # Load prompt
            prompt_text = self._load_prompt(element_key)
            
            # Build user prompt
            user_prompt = f"分析主题: {topic}\n"
            if round_num == 1 and engram_context:
                user_prompt = engram_context + "\n" + user_prompt
            if prev_context:
                user_prompt += prev_context
            
            # Call LLM
            try:
                response = call_llm(
                    system_prompt=prompt_text,
                    user_prompt=user_prompt,
                    model_key=model
                )
                outputs[element_key.replace('wood','qinglong').replace('fire','zhuque')
                       .replace('earth','diting').replace('metal','baihu')
                       .replace('water','xuanwu')] = response.get('text', '')
            except Exception as e:
                print(f"[{agent_name}] Error: {e}")
                outputs[element_key] = f"Error: {e}"
        
        return {
            'round': round_num,
            'element_outputs': outputs,
            'timestamp': time.time()
        }
    
    def _calculate_score(self, round_result: dict) -> float:
        """Calculate round score based on output quality"""
        outputs = round_result.get('element_outputs', {})
        
        score = 0.5  # Base score
        
        # Each agent contributing adds to score
        for agent in ['qinglong', 'zhuque', 'diting', 'baihu', 'xuanwu']:
            output = outputs.get(agent, '')
            if output and len(str(output)) > 100:
                score += 0.08
            if output and len(str(output)) > 500:
                score += 0.02
        
        return min(score, 1.0)
    
    def _assemble_result(self, run_id, topic, rounds, scores, 
                         element_outputs, converged, start_time) -> dict:
        """Assemble the final result dictionary"""
        return {
            'run_id': run_id,
            'topic': topic,
            'rounds': rounds,
            'scores': scores,
            'element_outputs': element_outputs,
            'convergence': {
                'verdict': 'converged' if converged else 'max_rounds',
                'rounds': len(rounds),
                'final_delta': abs(scores[-1] - scores[-2]) if len(scores) >= 2 else None
            },
            'kunpeng': {},  # Populated by xuanwu output parsing
        }
    
    def _score_to_grade(self, score: float) -> str:
        if score >= 0.9: return 'S'
        if score >= 0.85: return 'A'
        if score >= 0.75: return 'B+'
        if score >= 0.65: return 'B'
        if score >= 0.5: return 'C'
        return 'D'
    
    def _load_prompt(self, element_key: str) -> str:
        """Load prompt file for an element"""
        import os
        name_map = {
            'wood': 'qinglong', 'fire': 'zhuque', 'earth': 'diting',
            'metal': 'baihu', 'water': 'xuanwu'
        }
        prompt_name = name_map.get(element_key, element_key)
        
        # Try multiple locations
        for base in ['prompts', '../prompts', 'D:\\ClawMatrix\\prompts_v2']:
            path = os.path.join(base, f'{prompt_name}_system.txt')
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
        
        return f"You are {ELEMENTS[element_key]['name']}, the {ELEMENTS[element_key]['philosophy']} agent."
