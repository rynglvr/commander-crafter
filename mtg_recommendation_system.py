# mtg_recommendation_system.py
# Standalone module for the MTG Commander Recommendation System

import pandas as pd
import numpy as np
import pickle
import ast
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings('ignore')

class MTGCommanderRecommendationSystem:
    """
    MTG Commander recommendation system using oracle text similarity + pattern boosting
    
    Features:
    - Oracle text similarity via TF-IDF + cosine similarity
    - Keyword consensus boosting (80% threshold, configurable boost)
    - Secondary type consensus boosting (80% threshold, configurable boost)
    - Power/toughness pattern boosting (configurable boosts)
    - Known recommendation penalty (configurable, default -15%)
    - Short oracle text penalty (configurable, default -10% for <40 characters)
    - Color identity validation
    
    All scoring parameters are configurable via initialization parameters.
    """
    
    def __init__(self, tfidf, commander_patterns, creatures_df, features_df,
                 keyword_boost=0.1, type_boost=0.1, power_boost=0.05, 
                 toughness_boost=0.05, known_penalty=0.85, short_text_penalty=0.90):
        self.tfidf = tfidf
        self.commander_patterns = commander_patterns
        self.creatures_df = creatures_df
        self.features_df = features_df
        
        # Store configurable scoring parameters
        self.keyword_boost = keyword_boost
        self.type_boost = type_boost
        self.power_boost = power_boost
        self.toughness_boost = toughness_boost
        self.known_penalty = known_penalty
        self.short_text_penalty = short_text_penalty
        
        print("🧠 Precomputing creature embeddings...")
        self._precompute_embeddings()
        print(f"✅ System ready with {len(self.creatures_df):,} creatures")
        print(f"📊 Scoring config: keyword={keyword_boost}, type={type_boost}, "
              f"power={power_boost}, toughness={toughness_boost}")
    
    def _precompute_embeddings(self):
        """Precompute TF-IDF embeddings for all creatures"""
        creature_texts = self.creatures_df['oracle_text_clean'].fillna('')
        self.creature_embeddings = self.tfidf.transform(creature_texts).toarray()
    
    def _get_power_toughness_patterns(self, commander_recs):
        """Analyze power/toughness patterns for boosting rules"""
        patterns = {'high_power_boost': False, 'low_power_boost': False, 'high_toughness_boost': False}
        
        if len(commander_recs) == 0:
            return patterns
        
        # Get P/T data for recommended creatures
        pt_data = []
        for _, rec in commander_recs.iterrows():
            creature = self.creatures_df[self.creatures_df['name'] == rec['recommended_creature']]
            if len(creature) > 0:
                pt_data.append((creature.iloc[0]['power_clean'], creature.iloc[0]['toughness_clean']))
        
        if not pt_data:
            return patterns
        
        total = len(pt_data)
        powers, toughnesses = zip(*pt_data)
        
        # Apply pattern rules
        if sum(1 for p in powers if p >= 4) / total >= 0.75:
            patterns['high_power_boost'] = True
        if sum(1 for p in powers if p <= 2) / total >= 0.75:
            patterns['low_power_boost'] = True
        if sum(1 for p, t in pt_data if t > p) / total >= 0.80:
            patterns['high_toughness_boost'] = True
        
        return patterns
    
    def _is_valid_color_identity(self, creature_colors, commander_colors):
        """Validate MTG color identity rules"""
        if not creature_colors:  # Colorless is always valid
            return True
        if not commander_colors:  # Colorless commander can only play colorless
            return False
        return set(creature_colors).issubset(set(commander_colors))
    
    def get_recommendations(self, commander_name, top_k=100, include_known=True):
        """
        Get recommendations for a commander
        
        Args:
            commander_name: Name of the commander
            top_k: Number of recommendations to return
            include_known: Whether to include known recommendations (with penalty)
        
        Returns:
            List of recommendation dictionaries with scores and boost details
        """
        
        # Get training data for this commander
        commander_recs = self.features_df[self.features_df['commander'] == commander_name]
        if len(commander_recs) == 0:
            print(f"⚠️ No training data found for {commander_name}")
            return []
        
        # Get commander info
        commander_info = self.creatures_df[self.creatures_df['name'] == commander_name]
        if len(commander_info) == 0:
            print(f"⚠️ Commander {commander_name} not found in database")
            return []
        
        commander_colors = ast.literal_eval(commander_info.iloc[0]['color_identity_parsed'])
        
        # Get consensus patterns
        patterns = self.commander_patterns.get(commander_name, {})
        consensus_keywords = [kw for kw, _ in patterns.get('consensus_keywords', [])]
        consensus_types = [st for st, _ in patterns.get('consensus_types', [])]
        pt_patterns = self._get_power_toughness_patterns(commander_recs)
        
        # Calculate target embedding (average of known recommendations)
        rec_indices = []
        for _, rec in commander_recs.iterrows():
            idx = self.creatures_df[self.creatures_df['name'] == rec['recommended_creature']].index
            if len(idx) > 0:
                rec_indices.append(idx[0])
        
        if not rec_indices:
            print(f"⚠️ No valid recommendations found for {commander_name}")
            return []
        
        target_embedding = np.mean(self.creature_embeddings[rec_indices], axis=0)
        
        # Calculate similarities and apply boosts
        similarities = cosine_similarity([target_embedding], self.creature_embeddings)[0]
        recommendations = []
        known_creatures = set(commander_recs['recommended_creature'])
        
        for i, (similarity, creature) in enumerate(zip(similarities, self.creatures_df.itertuples())):
            # Skip commander itself
            if creature.name == commander_name:
                continue
            
            # Skip known recommendations if not including them
            is_known = creature.name in known_creatures
            if not include_known and is_known:
                continue
            
            # Validate color identity
            creature_colors = ast.literal_eval(creature.color_identity_parsed)
            if not self._is_valid_color_identity(creature_colors, commander_colors):
                continue
            
            # Start with base similarity
            score = similarity
            boosts = []
            
            # Apply keyword consensus boost
            creature_keywords = ast.literal_eval(creature.keywords_parsed) if creature.keywords_parsed else []
            if any(kw in creature_keywords for kw in consensus_keywords):
                score += self.keyword_boost
                boosts.append(f"Keyword +{self.keyword_boost:.2f}")
            
            # Apply secondary type consensus boost
            creature_types = str(creature.secondary_type).split() if creature.secondary_type else []
            for consensus_type in consensus_types:
                if consensus_type in creature_types:
                    score += self.type_boost
                    boosts.append(f"Type({consensus_type}) +{self.type_boost:.2f}")
                    break
            
            # Apply power/toughness pattern boosts
            if pt_patterns['high_power_boost'] and creature.power_clean >= 4:
                score += self.power_boost
                boosts.append(f"HighPower +{self.power_boost:.2f}")
            if pt_patterns['low_power_boost'] and creature.power_clean <= 2:
                score += self.power_boost
                boosts.append(f"LowPower +{self.power_boost:.2f}")
            if pt_patterns['high_toughness_boost'] and creature.toughness_clean > creature.power_clean:
                score += self.toughness_boost
                boosts.append(f"HighToughness +{self.toughness_boost:.2f}")
            
            # Apply penalties
            penalties = []
            if is_known:
                score *= self.known_penalty
                penalty_pct = (1 - self.known_penalty) * 100
                penalties.append(f"Known -{penalty_pct:.0f}%")
            
            oracle_length = len(str(creature.oracle_text_clean)) if creature.oracle_text_clean else 0
            if oracle_length < 40:
                score *= self.short_text_penalty
                penalty_pct = (1 - self.short_text_penalty) * 100
                penalties.append(f"ShortText -{penalty_pct:.0f}%")
            
            recommendations.append({
                'creature_name': creature.name,
                'base_similarity': similarity,
                'final_score': score,
                'boosts': boosts,
                'penalties': penalties,
                'is_known': is_known,
                'power_toughness': f"{creature.power_clean:.0f}/{creature.toughness_clean:.0f}",
                'oracle_length': oracle_length
            })
        
        # Sort by final score and return top K
        recommendations.sort(key=lambda x: x['final_score'], reverse=True)
        return recommendations[:top_k]
    
    def get_commander_info(self, commander_name):
        """Get analysis info for a commander"""
        commander_recs = self.features_df[self.features_df['commander'] == commander_name]
        if len(commander_recs) == 0:
            return None
        
        patterns = self.commander_patterns.get(commander_name, {})
        pt_patterns = self._get_power_toughness_patterns(commander_recs)
        
        return {
            'total_recommendations': len(commander_recs),
            'consensus_keywords': patterns.get('consensus_keywords', []),
            'consensus_types': patterns.get('consensus_types', []),
            'power_toughness_patterns': pt_patterns
        }

def create_recommendation_system(keyword_boost=0.1, type_boost=0.1, 
                                power_boost=0.05, toughness_boost=0.05,
                                known_penalty=0.85, short_text_penalty=0.90):
    """
    Create and return a new recommendation system by loading all required data
    
    Args:
        keyword_boost: Boost for keyword consensus matches (default: 0.1)
        type_boost: Boost for secondary type consensus matches (default: 0.1)
        power_boost: Boost for power pattern matches (default: 0.05)
        toughness_boost: Boost for toughness pattern matches (default: 0.05)
        known_penalty: Multiplier penalty for known recommendations (default: 0.85 = -15%)
        short_text_penalty: Multiplier penalty for short oracle text (default: 0.90 = -10%)
    
    Returns:
        MTGCommanderRecommendationSystem: Configured recommendation system
    """
    print("🃏 Loading MTG Commander Recommendation System...")
    
    # Load all required data
    features_df = pd.read_csv('data/processed/training_features.csv')
    creatures_df = pd.read_csv('data/processed/creatures_processed.csv')
    
    with open('data/processed/tfidf_vectorizer.pkl', 'rb') as f:
        tfidf = pickle.load(f)
    
    with open('data/processed/commander_patterns.pkl', 'rb') as f:
        commander_patterns = pickle.load(f)
    
    print(f"✅ Loaded {features_df.shape[0]:,} training examples")
    print(f"✅ Loaded {creatures_df.shape[0]:,} creatures")
    
    # Create and return the system with custom parameters
    return MTGCommanderRecommendationSystem(
        tfidf=tfidf,
        commander_patterns=commander_patterns,
        creatures_df=creatures_df,
        features_df=features_df,
        keyword_boost=keyword_boost,
        type_boost=type_boost,
        power_boost=power_boost,
        toughness_boost=toughness_boost,
        known_penalty=known_penalty,
        short_text_penalty=short_text_penalty
    )