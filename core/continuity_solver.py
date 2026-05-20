# AI Film Director Engine - Narrative Continuity Solver
import os
import json

class NarrativeContinuitySolver:
    def __init__(self, annotations_path=r"c:\TEST\cache\clip_annotations.json"):
        self.annotations_path = annotations_path
        self.annotations = {}
        self.load_annotations()

    def load_annotations(self):
        """
        Loads the structured clip annotations database from disk.
        """
        if os.path.exists(self.annotations_path):
            try:
                with open(self.annotations_path, "r", encoding="utf-8") as f:
                    self.annotations = json.load(f)
                print(f"   🧠 [Continuity Solver] Successfully loaded {len(self.annotations)} clip annotations.")
            except Exception as e:
                print(f"   ⚠️ [Continuity Solver] Warning: Failed to load annotations: {e}")
        else:
            print("   ⚠️ [Continuity Solver] Warning: clip_annotations.json not found. Running in neutral bypass mode.")

    def score_candidate(self, candidate_name, role, history_seq, next_clip_info=None, config_rules=None):
        """
        Computes the narrative continuity score adjustment for a candidate clip.
        
        Args:
            candidate_name (str): Filename of the candidate (e.g., 'C0264.MP4').
            role (str): Narrative role of the beat ('setup', 'detail', 'catwalk', 'finale').
            history_seq (list): List of dictionaries of already selected clips on the timeline.
            next_clip_info (dict, optional): Selected attributes of the subsequent clip (used for Reroll).
            config_rules (dict, optional): Custom continuity rules parsed from the JSON configuration.
            
        Returns:
            float: Score adjustment (positive bonus or negative penalty).
        """
        basename = os.path.basename(candidate_name)
        annotation = self.annotations.get(basename, {})
        
        cand_char = annotation.get("character", "product_or_booth")
        cand_act = annotation.get("action", "product_holding")
        
        # Default rules parameters
        min_contiguous = 3
        lock_bonus = 1.8
        fatigue_penalty = -0.8
        
        action_rules = [
            {
                "trigger_action": "spray",
                "prevent_repeat": True,
                "repeat_penalty": -3.0,
                "prefer_next_actions": ["combing", "product_holding", "product_closeup"],
                "prefer_bonus": 1.2
            },
            {
                "trigger_action": "shampoo",
                "prevent_repeat": True,
                "repeat_penalty": -3.0,
                "prefer_next_actions": ["combing", "spray"],
                "prefer_bonus": 1.2
            }
        ]
        
        # Override rules with JSON config if available
        if config_rules:
            char_lock_cfg = config_rules.get("character_locking", {})
            min_contiguous = char_lock_cfg.get("min_contiguous_cuts", min_contiguous)
            lock_bonus = char_lock_cfg.get("lock_bonus", lock_bonus)
            fatigue_penalty = char_lock_cfg.get("fatigue_penalty", fatigue_penalty)
            action_rules = config_rules.get("action_causality", action_rules)
            
        score_adjustment = 0.0
        
        # ----------------------------------------------------
        # 1. Chronological Character Continuity Lock & Alternation
        # ----------------------------------------------------
        if history_seq:
            prev_clip = history_seq[-1]
            prev_char = prev_clip.get("character", "product_or_booth")
            
            if prev_char != "product_or_booth":
                # Count consecutive occurrences of this character backwards
                consecutive_count = 0
                for clip in reversed(history_seq):
                    if clip.get("character") == prev_char:
                        consecutive_count += 1
                    else:
                        break
                        
                if consecutive_count < min_contiguous:
                    # Character Lock is active!
                    if cand_char == prev_char:
                        score_adjustment += lock_bonus  # Keep showing the same character
                    elif cand_char != "product_or_booth":
                        score_adjustment -= 2.0         # Heavy penalty for switching to another character
                else:
                    # Character lock is satisfied. Give a slight penalty to avoid showing them forever.
                    if consecutive_count >= min_contiguous + 1:
                        if cand_char == prev_char:
                            score_adjustment += fatigue_penalty  # Slight discouragement to stay on same character
            
            # ----------------------------------------------------
            # 2. Action Causality Flow
            # ----------------------------------------------------
            prev_act = prev_clip.get("action", "product_holding")
            
            for rule in action_rules:
                trigger = rule.get("trigger_action")
                if prev_act == trigger:
                    # Handle repetition prevention
                    if cand_act == trigger and rule.get("prevent_repeat", True):
                        score_adjustment += rule.get("repeat_penalty", -3.0)
                    
                    # Handle preferred transition actions
                    preferred = rule.get("prefer_next_actions", [])
                    if cand_act in preferred:
                        score_adjustment += rule.get("prefer_bonus", 1.2)
            
            # General mild penalty to prevent consecutive identical actions to maintain visual rhythm
            if cand_act == prev_act:
                score_adjustment -= 0.5
                
        # ----------------------------------------------------
        # 3. Bi-directional Constraints for Contextual Reroll
        # ----------------------------------------------------
        if next_clip_info:
            next_char = next_clip_info.get("character", "product_or_booth")
            next_act = next_clip_info.get("action", "product_holding")
            
            # Preceding character check if history_seq is present
            if history_seq:
                prev_clip = history_seq[-1]
                prev_char = prev_clip.get("character", "product_or_booth")
                
                # Double-lock sandwich check: k-1 and k+1 feature the same character
                if prev_char == next_char and prev_char != "product_or_booth":
                    if cand_char == prev_char:
                        score_adjustment += 3.0  # Strongly lock the sandwich
                    elif cand_char != "product_or_booth":
                        score_adjustment -= 5.0  # Avoid inserting a different model in between
            
            # Check following action causality compatibility
            for rule in action_rules:
                trigger = rule.get("trigger_action")
                if cand_act == trigger:
                    # If this candidate is a trigger (like spray) and next is also a trigger, penalize
                    if next_act == trigger and rule.get("prevent_repeat", True):
                        score_adjustment += rule.get("repeat_penalty", -3.0)
                    # Encourage transitioning into next
                    preferred = rule.get("prefer_next_actions", [])
                    if next_act in preferred:
                        score_adjustment += rule.get("prefer_bonus", 1.2)
                        
        return score_adjustment
