# Video Agent Architecture Reference

Operational reference for building an autonomous video creation agent. Based on the full landscape survey of video decomposition and recreation tools (Feb 2026).

---

## 1. Core Reality

**No single system exists** that takes a reference video and faithfully recreates it end-to-end without human involvement. But all components exist separately. Our job: build the orchestrator.

**Realistic expectations:**
- Short-form (<60s), semi-automated: **70-80% fidelity** to reference
- Fully autonomous (no human review): **50-60% fidelity**
- Content >2 min: human creative direction at scene-planning stage remains essential
- Prediction: 60s autonomous at 85%+ fidelity by late 2026

---

## 2. Pipeline Architecture (5 Stages)

```
Reference Video
    |
    v
[Stage 1: PREPROCESSING]
    PySceneDetect / TransNetV2 --> shot segmentation + timestamps
    Demucs --> audio separation (vocals/drums/bass/other)
    Whisper + pyannote-audio --> speech transcription + speaker diarization
    Key frame extraction at boundaries + intervals
    |
    v
[Stage 2: VLM ANALYSIS]
    Gemini 2.5 Pro (primary) --> structured scene descriptions
    - 84.8% VideoMME, 6hr video, 2M-token context
    - Low-res mode: 66 tokens/frame, 0.5% perf drop
    Fallbacks: Qwen2.5-VL-72B (best JSON output), GPT-4o (per-frame)
    |
    v
[Stage 3: STRUCTURED DECOMPOSITION]
    LLM Orchestrator (Claude / GPT-4o) -->
    InstanceCap-format structured schema:
    - Per-instance: class / appearance / action / position
    - Global: background, camera movements
    - Shot-by-shot edit decision list with timestamps
    - Character identity cards (reference images + ArcFace embeddings)
    |
    v
[Stage 4: GENERATION]
    ComfyUI as orchestration layer
    Model routing based on content type (see Section 5)
    Character consistency: LoRA / IP-Adapter / ConsisID
    |
    v
[Stage 5: QA & REFINEMENT]
    CLIP similarity scoring (generated vs reference frames)
    ArcFace identity verification (cosine similarity threshold)
    VLM semantic comparison (Gemini 2.5 Pro)
    Selective re-generation of failed segments
```

---

## 3. Decomposition Schema (6 Layers)

Every reference video must be decomposed into these 6 layers:

### 3.1 Visual Layer
- Art style, rendering approach, color palette, saturation, contrast
- Color grading (warm/cool, LUT characteristics)
- Lighting (direction, intensity, type, shadows, time of day)
- Lens (focal length, distortion, DOF, bokeh)

### 3.2 Compositional Layer
- Camera movement (static, pan, tilt, dolly, tracking, crane, handheld, orbit)
- Framing (wide, full body, medium, close-up, extreme close-up)
- Compositional rules (rule of thirds, leading lines, symmetry)
- DOF intent, rack focus beats

### 3.3 Narrative Layer
- Scene boundaries (PySceneDetect / TransNetV2)
- Shot sequence and editing rhythm (cut frequency, avg shot duration)
- Pacing patterns (acceleration / deceleration)
- Transition types (hard cut, dissolve, fade, match cut)

### 3.4 Object Layer
- Characters: identity (ArcFace), costume, pose (OpenPose), expression
- Objects: props, vehicles, spatial relationships
- Backgrounds: environments, architecture, natural elements
- Extraction tools: SAM 2, GroundingDINO

### 3.5 Dynamic Layer
- Motion patterns (speed, direction, acceleration)
- Physics interactions (gravity, collisions, fluid)
- Inter-object interactions
- Tools: RAFT (optical flow), OnlyFlow (motion conditioning)

### 3.6 Audio Layer
- Speech: Whisper transcription + pyannote-audio diarization
- Music: Librosa analysis (tempo, key, instrumentation)
- Source separation: Demucs (Meta) — 9.20 dB SDR on MUSDB HQ
- Sound effects and ambient classification

---

## 4. Structured Video Manifest (JSON Output Format)

The decomposition output is a JSON manifest:

```json
{
  "metadata": {
    "source_duration": "00:00:45",
    "total_shots": 12,
    "resolution": "1920x1080",
    "fps": 24,
    "style_lut_intent": "warm cinematic, orange-teal grade"
  },
  "identity_anchors": [
    {
      "id": "char_01",
      "name": "Main Character",
      "reference_frames": ["frame_0042.jpg", "frame_0187.jpg"],
      "arcface_embedding": "...",
      "wardrobe": "dark blue suit, white shirt, no tie",
      "key_attributes": "male, 30s, short brown hair, beard"
    }
  ],
  "shots": [
    {
      "shot_id": 1,
      "timecode": { "start": "00:00:00.000", "end": "00:00:03.500" },
      "keyframes": { "start": "frame_0001.jpg", "end": "frame_0084.jpg" },
      "shot_type": "wide establishing",
      "subject": { "id": "char_01", "action": "walks toward camera" },
      "setting": "urban street, dusk, wet pavement reflections",
      "camera_movement": "slow dolly forward",
      "lighting": "golden hour backlight, warm practicals from storefronts",
      "style": "cinematic, shallow DOF, film grain",
      "audio": {
        "dialogue": null,
        "sfx": "ambient city, distant traffic",
        "music": "lo-fi piano, 85 BPM"
      },
      "transition_out": "hard cut"
    }
  ]
}
```

---

## 5. Generation Model Selection Matrix

### Decision Tree
```
What are you recreating?
    |
    +--> Need editing-style faithfulness (keep composition, tweak objects)?
    |       --> VACE + Wan stack (open-source, max control)
    |
    +--> Need cinematic quality + audio?
    |       --> Veo 3.1 ($0.20-$0.40/sec)
    |
    +--> Need multi-shot storyboard + character consistency?
    |       --> Kling 3.0 (up to 5 shots/pass, $0.01-$0.14/sec)
    |
    +--> Need maximum pipeline control + customization?
    |       --> Wan 2.1/2.2 (open-source, Apache 2.0, runs on RTX 4090)
    |
    +--> Need multi-modal reference inputs?
            --> Seedance 2.0 (up to 9 ref images + 3 video clips + 3 audio tracks)
            --> NOTE: IP controversy risk, evaluate before using at scale
```

### Model Comparison

| Model | Best For | Max Duration | Audio | Multi-shot | API Price | API Access |
|-------|----------|-------------|-------|------------|-----------|------------|
| **Kling 3.0** | Multi-shot storyboards, character consistency | 15s | Native | 5 shots/pass | $0.01-$0.14/sec | fal.ai, native API |
| **Veo 3.1** | Cinematic quality, dialogue + lip-sync | ~10s | Native (dialogue, SFX, ambient, music) | Via extension | $0.20-$0.40/sec | Gemini API, Vertex AI |
| **Sora 2** | Creative exploration, remix iterations | 25s | Native | Limited | OpenAI API | OpenAI API |
| **Wan 2.1/2.2** | Pipeline control, LoRA/ControlNet, open-source | Varies | Via V2A variant | Via orchestration | Self-hosted / fal.ai | Open-source + fal.ai |
| **Seedance 2.0** | Reference-driven recreation, multi-modal input | ~10s | Native joint gen | Native cuts/transitions | Via API | ByteDance API |
| **Luma Ray 3.14** | Start/end keyframe control, HDR | ~10s | Limited | Limited | Luma API | Luma API |
| **Runway Gen-4.5** | Prompt adherence, camera choreography | ~10s | Limited | Limited | Runway API | Runway API |

### Character Consistency Strategy

| Method | When to Use | Requirements |
|--------|-------------|-------------|
| **LoRA training** | Main characters, highest quality | 10-20 reference images, different angles |
| **IP-Adapter FaceID Plus V2** | Supporting characters | Single reference image |
| **ConsisID** | Zero-shot identity preservation | No training needed, DiT-based generators |
| **InstantID** | Quick face transfer | Single reference image |

### Aggregated API Access
**fal.ai** — unified interface to 600+ models including Kling 3.0, Veo 3.1, Sora 2, Wan 2.6, Seedance 2.0, Hailuo 2.3. Essential for a pipeline that routes different content to different models.

---

## 6. Commercial Video-to-Prompt Tools (Decomposition)

### Tier 1: Full Pipeline Tools
| Tool | Strength | Output Format | Pricing |
|------|----------|--------------|---------|
| **Short.AI** | Only analyze→edit→regenerate platform. Frame-by-frame + shot-by-shot. Character profiles for cross-shot consistency | Structured scenes | Check site |
| **Video2Prompt.org** | Precise timestamps, JSON exports, shot bundles for batch gen | JSON, Text bundles | Check site |
| **PromptAI Videos** | ViT-based, model-specific prompt optimization, detects AI-generated source | Model-specific prompts | Check site |

### Tier 2: Specialized Tools
| Tool | Strength |
|------|----------|
| **Vidtofy** | Per-platform parameter formatting (Sora, Kling, Veo, Runway, Pika) |
| **TopYappers** | Integrated viral content database for trend discovery |
| **Vora (FineShare)** | Direct Sora 2 integration for one-click recreation |
| **video-to-prompt.com** | Gemini-powered, /scenes endpoint for multi-scene breakdown |
| **IndieGTM** | Free, visual DNA extraction |

### Tier 3: Structured Template
| Tool | Strength |
|------|----------|
| **Pickaxe AI Video Prompt Architect** | Most rigorous prompt schema: 6-state workflow + 8-part framework |

---

## 7. Prompt Template (Cross-Model)

The universal template that maps to all major model prompt guides:

```
1. Shot type + framing + lens intent
2. Subject definition (with persistent attributes / ID reference)
3. Single primary action (per shot)
4. Setting + time + mood
5. Camera movement (one clear move)
6. Lighting + color grade + texture (grain, film stock)
7. Motion detail (beats / timing)
8. Audio (dialogue + SFX + ambience) — when supported
9. Negative constraints — when platform supports it
```

### Model-Specific Prompt Patterns

**Runway Gen-4.5:** `[camera movement]: [establishing scene]. [additional details].`
Handles complex sequenced instructions and detailed camera choreography.

**Kling 3.0:** Subject → Movement → Scene → Camera Language → Lighting
Explicit camera movement controls (multiple movement types + "Master Shots").

**Veo 3.1:** Subject + Action + Setting + Camera + Lighting + Style + Audio cues + Constraints
Reference images and extension for multi-shot consistency.

**Sora 2:** Iterative "remix" approach — isolate the variable you change.
Lens changes ("switch to 85mm"), lighting/palette adjustments.

---

## 8. Open-Source Building Blocks

### Analysis & Preprocessing
| Tool | Function | Status |
|------|----------|--------|
| **PySceneDetect** | Content-aware scene/shot detection (CLI + Python) | Production OSS |
| **TransNetV2** | Neural shot boundary detection | Research OSS, widely used |
| **SAM 2** | Promptable video segmentation with streaming memory | Research + OSS |
| **ByteTrack** | Multi-object tracking (tracking-by-detection) | Research→production |
| **RAFT** | Optical flow estimation | Production OSS |
| **GroundingDINO** | Open-vocabulary object detection | Production OSS |
| **OpenPose** | Human pose estimation | Production OSS |
| **ArcFace** | Face recognition embeddings | Production OSS |

### Audio
| Tool | Function | Status |
|------|----------|--------|
| **Whisper** | Speech transcription | Production (OpenAI) |
| **pyannote-audio** | Speaker diarization | Production OSS |
| **Demucs** | Source separation (9.20 dB SDR) | Production (Meta) |
| **Librosa** | Music analysis (tempo, key, instruments) | Production OSS |

### Generation & Composition
| Tool | Function | Status |
|------|----------|--------|
| **ComfyUI** | Visual workflow orchestration for generation | Production OSS |
| **VACE** | Unified creation + editing (VCU + Context Adapter) on Wan 2.1 | Research + OSS |
| **ConsisID** | Identity preservation via frequency decomposition | Research (CVPR 2025) |
| **Stable Video Infinity** | Infinite-length gen via error recycling | Research + OSS (ICLR 2026) |
| **InstantID** | Zero-shot face transfer | Production OSS |
| **IP-Adapter** | Image prompt adapter for diffusion models | Production OSS |

### Academic Frameworks (Reference Architectures)
| Framework | Key Idea | Why It Matters |
|-----------|----------|----------------|
| **VideoDirectorGPT** | GPT-4 → scenes + entities + layouts + consistency groups | Canonical decomposition pattern |
| **InstanceCap** | Per-instance structured descriptions (class/appearance/action) | Best validated decomposition schema |
| **CoAgent** | Plan → Synthesize → Verify → Edit loop | Correct architectural pattern for our agent |
| **DreamFactory** | Multi-agent filmmaking + cross-scene QA metrics | QA methodology reference |
| **MAViS** | Script→shots→characters→keyframes→video→audio | End-to-end long-sequence reference |

---

## 9. Known Limitations & Workarounds

| Limitation | Severity | Workaround |
|-----------|----------|------------|
| **Temporal coherence >25s** | Critical | Generate per-shot, use Stable Video Infinity for stitching, or Kling 3.0 multi-shot (up to 15s) |
| **Identity drift across shots** | High | LoRA for main characters, ConsisID for zero-shot, ArcFace verification loop |
| **Exact camera trajectory** | High | Approximate via camera-language prompts; CameraCtrl for research-grade precision |
| **Multi-clip seam artifacts** | Medium | Kling 3.0 single-generation storyboard (6 cuts), Wan 2.6 timeline-aware gen |
| **Physics accuracy (24.1% best)** | Medium | Accept visual plausibility over physical correctness; avoid complex physics scenes |
| **Hand artifacts** | Medium | Improved in 2026 but still glitchy; avoid hand close-ups when possible |
| **Text rendering** | Medium | Burn text in post-production, do not rely on model text generation |
| **Music recreation** | High | Unsolved in automated pipelines; use licensed music or Suno/Udio separately |
| **Style drift across sessions** | Medium | Detailed style descriptions + LoRA + reference images in every prompt |
| **Decomposition precision loss** | Inherent | Quantitative data (exact colors, exact camera speed) is lost; accept ~approximation |

---

## 10. Cost Estimation Framework

### Per-Video Cost Structure (60s video, ~12 shots)

| Stage | Tool | Estimated Cost |
|-------|------|---------------|
| Analysis | Gemini 2.5 Pro (video analysis) | $0.05-$0.50 |
| Decomposition | Claude / GPT-4o (orchestration) | $0.10-$0.30 |
| Generation (Kling 3.0) | 60s at $0.01-$0.14/sec | $0.60-$8.40 |
| Generation (Veo 3.1) | 60s at $0.20-$0.40/sec | $12.00-$24.00 |
| QA Pass | Gemini 2.5 Pro + CLIP | $0.05-$0.20 |
| Re-generation (30% fail rate) | ~20s regenerated | $0.20-$7.20 |
| **Total (Kling path)** | | **~$1.00-$16.60** |
| **Total (Veo path)** | | **~$12.40-$32.20** |

### Optimization Levers
- Use Wan 2.1/2.2 (self-hosted) to eliminate generation API costs
- Use Gemini low-res mode (66 tokens/frame) for analysis cost reduction
- Batch shot generation to reduce API overhead
- Use fal.ai for aggregated pricing across models

---

## 11. Agent Architecture Decision: How We Build This

### Architecture: CoAgent-Inspired Orchestrator

```
ContentAgent
    |
    +-- AnalysisAgent
    |       Uses: Gemini 2.5 Pro, PySceneDetect, Demucs, Whisper
    |       Output: Raw analysis data
    |
    +-- DecompositionAgent
    |       Uses: Claude / GPT-4o, SAM 2, ArcFace
    |       Output: Structured Video Manifest (JSON)
    |
    +-- GenerationAgent
    |       Uses: ComfyUI, fal.ai (Kling/Veo/Wan/Seedance routing)
    |       Input: Manifest + reference frames + identity cards
    |       Output: Generated video clips per shot
    |
    +-- QAAgent
    |       Uses: CLIP, ArcFace, Gemini 2.5 Pro
    |       Input: Generated clips + reference frames
    |       Output: Pass/fail per shot + regeneration instructions
    |
    +-- AssemblyAgent
            Uses: FFmpeg, audio mixing
            Input: Approved clips + audio tracks
            Output: Final video
```

### Required API Keys / Services
- **Google AI** (Gemini 2.5 Pro) — analysis + QA
- **fal.ai** — unified generation API (Kling, Veo, Wan, Seedance, Sora)
- **OpenAI** (optional) — GPT-4o for decomposition, Sora 2 for generation
- **Anthropic** (Claude) — decomposition orchestration (we are this)

### Required Local Tools
- Python 3.10+
- FFmpeg (video/audio processing)
- PySceneDetect, TransNetV2
- Demucs, Whisper, pyannote-audio, Librosa
- SAM 2, GroundingDINO, ArcFace, OpenPose
- ComfyUI (if using local generation with Wan)
- CLIP (for QA scoring)

---

## 12. Workflow Modes

### Mode A: Reference Video Recreation
```
Input:  Reference video (URL or file)
Goal:   Recreate the video as closely as possible
Flow:   Full pipeline (all 5 stages)
```

### Mode B: Script-to-Video
```
Input:  Text script / concept description
Goal:   Generate original video from scratch
Flow:   Skip Stage 1-2, use LLM for Stage 3, then Stage 4-5
```

### Mode C: Style Transfer
```
Input:  Reference video (style) + new script (content)
Goal:   Apply reference video's visual style to new content
Flow:   Stage 1-2 for style extraction only, Stage 3 merges style + new content
```

---

## 14. Additional Frameworks & Protocols (Feb 2026 Update)

### 14.1 VideoGen-of-Thought (VGoT) — NeurIPS 2025
- GitHub: github.com/DuNGEOnmassster/VideoGen-of-Thought
- Modular pipeline: Script Generation → Keyframe Generation → Shot-Level Video Generation → Smoothing
- **5-domain decomposition per shot** (most important — we integrate this into our pipeline):
  1. Character Dynamics (pcha) — character descriptions, appearance, traits
  2. Background Continuity — backgrounds and environments
  3. Relationship Evolution — inter-character interactions
  4. Camera Movements — camera behavior
  5. HDR Lighting — lighting and atmosphere
- Self-validation mechanism for logical coherence between shots
- Converts user prompt → brief shot descriptions → detailed cinematic specs per 5 domains

### 14.2 Video-As-Prompt (VAP) — ByteDance
- GitHub: github.com/bytedance/Video-As-Prompt
- Uses reference video as direct semantic prompt via plug-and-play Mixture-of-Transformers (MoT)
- Extracts: concept, style, motion, camera from reference
- Supports: multiple reference videos + one image; one video + multiple images; cross-scene semantic transfer
- Key for our "recreate" and "style_transfer" modes

### 14.3 VChain (Chain-of-Visual-Thought)
- 3-stage pipeline: Visual Thought Reasoning via GPT-4o
- Causal chain of events → iterative keyframe generation
- Useful for script-to-video mode: reason about logical visual progression

### 14.4 Lights, Camera, Consistency — "Filmmaker Pipeline"
- LLM generates detailed production screenplay → T2I creates consistent character visuals → these serve as "anchors" for each scene
- **JSON blueprints** for deterministic control — directly applicable to our manifest format
- Structured deterministic control ensures precise script adherence

### 14.5 New Decomposition Tools
| Tool | Key Capability |
|------|---------------|
| **Promptank.com** | Captures 85-95% of visual elements: composition, color correction, motion dynamics, camera, atmosphere |
| **TopYappers** | Frame-by-frame: scenes, subjects, lighting, camera, colors, audio → prompts for Sora, Veo, Runway, Pika |

### 14.6 Veo 3.1 Official Prompt Formula
5-part formula: `[Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]`
Source: Google Cloud official documentation

---

## 13. Key References

| Resource | URL | Use |
|----------|-----|-----|
| Short.AI | https://short.ai | Tier 1 decomposition |
| Video2Prompt.org | https://video2prompt.org | JSON export decomposition |
| PromptAI Videos | https://promptaivideos.com | Model-specific prompts |
| Pickaxe Architect | https://pickaxe.co/user/templates/pickaxe/ai-video-prompt-architect | Prompt schema reference |
| fal.ai | https://fal.ai | Aggregated generation API |
| VACE (GitHub) | https://github.com/ali-vilab/VACE | Unified generation + editing |
| ConsisID | https://arxiv.org/abs/2411.17440 | Identity preservation |
| Stable Video Infinity | https://github.com/vita-epfl/Stable-Video-Infinity | Long-form generation |
| InstanceCap | CVPR 2025 | Decomposition schema |
| CoAgent | arXiv Dec 2025 | Pipeline architecture pattern |
| PySceneDetect | https://github.com/Breakthrough/PySceneDetect | Shot detection |
| SAM 2 | https://arxiv.org/abs/2408.00714 | Video segmentation |
| VGoT | github.com/DuNGEOnmassster/VideoGen-of-Thought | 5-domain decomposition + self-validation |
| VAP (ByteDance) | github.com/bytedance/Video-As-Prompt | Reference video as semantic prompt |
| VChain | arXiv | Chain-of-visual-thought keyframe reasoning |
| Promptank.com | https://promptank.com | 85-95% visual element capture |
