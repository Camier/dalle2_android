"""
Style Presets for quick and consistent image generation
"""

from typing import Dict, Any, List
import json
from pathlib import Path

class StylePresetManager:
    """Manage artistic style presets for DALL-E generation"""
    
    def __init__(self, presets_file: str = "style_presets.json"):
        self.presets_file = Path(presets_file)
        self.presets = self._load_presets()
        
    def _load_presets(self) -> Dict[str, Dict[str, Any]]:
        """Load presets from file or create defaults"""
        if self.presets_file.exists():
            try:
                with open(self.presets_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Default presets
        return {
            "photorealistic": {
                "name": "Photorealistic",
                "description": "Ultra-realistic photography style",
                "modifiers": ["photorealistic", "8k resolution", "professional photography", 
                            "sharp focus", "natural lighting"],
                "negative_prompts": ["cartoon", "drawing", "painting", "illustration"],
                "params": {"quality": "hd"}
            },
            "oil_painting": {
                "name": "Oil Painting",
                "description": "Classic oil painting style",
                "modifiers": ["oil painting", "canvas texture", "brush strokes visible", 
                            "classical art style", "museum quality"],
                "negative_prompts": ["digital", "photo", "3D render"],
                "params": {}
            },
            "anime": {
                "name": "Anime/Manga",
                "description": "Japanese anime and manga style",
                "modifiers": ["anime style", "manga art", "cel shaded", "vibrant colors"],
                "negative_prompts": ["realistic", "photo", "western cartoon"],
                "params": {}
            },
            "watercolor": {
                "name": "Watercolor",
                "description": "Soft watercolor painting style",
                "modifiers": ["watercolor painting", "soft edges", "paper texture", 
                            "flowing colors", "artistic"],
                "negative_prompts": ["sharp", "digital", "photo"],
                "params": {}
            },
            "cyberpunk": {
                "name": "Cyberpunk",
                "description": "Futuristic cyberpunk aesthetic",
                "modifiers": ["cyberpunk style", "neon lights", "futuristic", 
                            "high tech", "dystopian"],
                "negative_prompts": ["medieval", "ancient", "natural"],
                "params": {}
            },
            "minimalist": {
                "name": "Minimalist",
                "description": "Clean minimalist design",
                "modifiers": ["minimalist style", "simple", "clean lines", 
                            "negative space", "modern design"],
                "negative_prompts": ["complex", "detailed", "busy", "cluttered"],
                "params": {}
            },
            "retro_80s": {
                "name": "Retro 80s",
                "description": "1980s retro aesthetic",
                "modifiers": ["80s style", "retro", "synthwave", "neon colors", 
                            "vintage aesthetic"],
                "negative_prompts": ["modern", "contemporary", "minimalist"],
                "params": {}
            },
            "sketch": {
                "name": "Pencil Sketch",
                "description": "Hand-drawn pencil sketch",
                "modifiers": ["pencil sketch", "hand drawn", "black and white", 
                            "sketch lines", "artistic drawing"],
                "negative_prompts": ["color", "painted", "digital"],
                "params": {}
            }
        }
    
    def apply_preset(self, prompt: str, preset_name: str) -> Dict[str, Any]:
        """Apply a style preset to a prompt"""
        if preset_name not in self.presets:
            raise ValueError(f"Unknown preset: {preset_name}")
        
        preset = self.presets[preset_name]
        
        # Combine prompt with style modifiers
        enhanced_prompt = f"{prompt}, {', '.join(preset['modifiers'])}"
        
        # Add negative prompts if supported
        result = {
            "prompt": enhanced_prompt,
            "style": preset_name,
            "params": preset.get("params", {})
        }
        
        if preset.get("negative_prompts"):
            result["negative_prompt"] = ", ".join(preset["negative_prompts"])
        
        return result
    
    def get_all_presets(self) -> List[Dict[str, Any]]:
        """Get list of all available presets"""
        return [
            {
                "id": key,
                "name": preset["name"],
                "description": preset["description"]
            }
            for key, preset in self.presets.items()
        ]
    
    def create_custom_preset(self, name: str, preset_data: Dict[str, Any]):
        """Create a custom preset"""
        self.presets[name] = preset_data
        self._save_presets()
    
    def _save_presets(self):
        """Save presets to file"""
        with open(self.presets_file, 'w') as f:
            json.dump(self.presets, f, indent=2)

class PromptEnhancer:
    """Enhance prompts with artistic and technical improvements"""
    
    def __init__(self):
        self.enhancement_templates = {
            "composition": [
                "rule of thirds composition",
                "golden ratio",
                "symmetrical composition",
                "dynamic angle",
                "bird's eye view",
                "close-up shot"
            ],
            "lighting": [
                "golden hour lighting",
                "dramatic lighting",
                "soft diffused light",
                "rim lighting",
                "chiaroscuro",
                "ambient occlusion"
            ],
            "quality": [
                "highly detailed",
                "4k resolution",
                "award winning",
                "trending on artstation",
                "masterpiece",
                "professional quality"
            ],
            "mood": [
                "atmospheric",
                "moody",
                "ethereal",
                "dramatic",
                "serene",
                "mystical"
            ]
        }
    
    def enhance_prompt(self, base_prompt: str, enhancements: List[str]) -> str:
        """Apply enhancements to a base prompt"""
        enhancement_modifiers = []
        
        for category in enhancements:
            if category in self.enhancement_templates:
                # Pick appropriate enhancement from category
                enhancement_modifiers.extend(self.enhancement_templates[category][:2])
        
        if enhancement_modifiers:
            return f"{base_prompt}, {', '.join(enhancement_modifiers)}"
        
        return base_prompt
    
    def suggest_enhancements(self, prompt: str) -> List[str]:
        """Suggest enhancements based on prompt analysis"""
        suggestions = []
        
        # Simple keyword analysis
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ["portrait", "person", "face"]):
            suggestions.extend(["lighting", "composition"])
        
        if any(word in prompt_lower for word in ["landscape", "scenery", "nature"]):
            suggestions.extend(["composition", "mood", "quality"])
        
        if any(word in prompt_lower for word in ["art", "painting", "drawing"]):
            suggestions.extend(["quality", "mood"])
        
        return list(set(suggestions))  # Remove duplicates
