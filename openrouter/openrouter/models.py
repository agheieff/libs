from __future__ import annotations
import os
import time
import json
from typing import TypedDict, NotRequired, List, Dict, Literal, Optional, Callable, Any

import httpx

# Lightweight, optional model catalog utilities for OpenRouter


class PricingHint(TypedDict, total=False):
    input_per_million: float
    output_per_million: float
    currency: str
    last_verified_at: str
    pricing_source: str


class ModalityFlags(TypedDict):
    text: bool
    vision: bool
    audio_in: bool
    audio_out: bool


class FeatureFlags(TypedDict):
    json_mode: bool
    tool_use: bool
    function_call: bool
    reasoning: bool


class Tiers(TypedDict):
    quality: Literal["low", "mid", "high"]
    speed: Literal["fast", "balanced", "slow"]


class Limits(TypedDict, total=False):
    tpm: int
    rpm: int


class ModelSpec(TypedDict, total=False):
    id: str
    provider: str
    label: str
    family: str
    context_window: int
    max_output_tokens: int
    modalities: ModalityFlags
    features: FeatureFlags
    tiers: Tiers
    pricing: PricingHint
    limits: Limits
    meta: Dict[str, Any]


Catalog = List[ModelSpec]


class ValidationError(ValueError):
    pass


_MODELS_ENDPOINT = "https://openrouter.ai/api/v1/models"
_CACHE: Dict[str, Any] = {"ts": 0.0, "ttl": 0, "data": []}


def _or_headers() -> Dict[str, str]:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set.")
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    app_title = os.getenv("OPENROUTER_APP_TITLE", "Arcadia AI Chat")
    headers["X-Title"] = app_title
    if ref := os.getenv("OPENROUTER_REFERER"):
        headers["HTTP-Referer"] = ref
    return headers


def _provider_from_id(mid: str) -> str:
    return mid.split("/", 1)[0] if "/" in mid else "unknown"


def _family_from_id(mid: str) -> str:
    return _provider_from_id(mid)


def _bool(v: Optional[bool]) -> bool:
    return bool(v)


def _default_modalities(*, vision: bool = False) -> ModalityFlags:
    return {"text": True, "vision": vision, "audio_in": False, "audio_out": False}


def _default_features(*, reasoning: bool = False) -> FeatureFlags:
    return {
        "json_mode": True,
        "tool_use": True,
        "function_call": True,
        "reasoning": reasoning,
    }


def _mk_spec(
    mid: str,
    *,
    label: Optional[str] = None,
    family: Optional[str] = None,
    context_window: int = 128_000,
    max_output_tokens: int = 8_192,
    modalities: Optional[ModalityFlags] = None,
    features: Optional[FeatureFlags] = None,
    quality: Literal["low", "mid", "high"] = "mid",
    speed: Literal["fast", "balanced", "slow"] = "balanced",
    pricing: Optional[PricingHint] = None,
    limits: Optional[Limits] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> ModelSpec:
    return {
        "id": mid,
        "provider": _provider_from_id(mid),
        "label": label or mid,
        "family": family or _family_from_id(mid),
        "context_window": max(1, int(context_window)),
        "max_output_tokens": max(1, int(max_output_tokens)),
        "modalities": modalities or _default_modalities(),
        "features": features or _default_features(),
        "tiers": {"quality": quality, "speed": speed},
        "pricing": pricing or {
            "currency": "USD",
            "pricing_source": "unverified",
        },
        "limits": limits or {},
        "meta": meta or {},
    }


def get_default_catalog() -> Catalog:
    """Return the default catalog with your requested models.

    Pricing is provided as optional hints only; values may be absent.
    """
    now_src = {"pricing_source": "openrouter-2025-10-public"}

    def v(vision: bool = False, reasoning: bool = False):
        return _default_modalities(vision=vision), _default_features(reasoning=reasoning)

    out: Catalog = []

    # deepseek
    m, f = v()
    out.append(
        _mk_spec(
            "deepseek/deepseek-v3.2-exp",
            label="Deepseek V3.2 Experimental",
            modalities=m,
            features=f,
            quality="mid",
            speed="fast",
        )
    )

    # moonshot
    m, f = v()
    out.append(_mk_spec("moonshotai/kimi-k2-0905", label="Kimi K2 0905", modalities=m, features=f))

    # zhipu (glm)
    m, f = v()
    out.append(_mk_spec("z-ai/glm-4.6", label="GLM 4.6", modalities=m, features=f))

    # qwen text
    m, f = v()
    out.append(_mk_spec("qwen/qwen3-max", label="Qwen3 Max", modalities=m, features=f))

    # qwen vl (vision) - thinking + instruct
    m, f = v(vision=True, reasoning=True)
    out.append(
        _mk_spec(
            "qwen/qwen3-vl-235b-a22b-thinking",
            label="Qwen3 VL 235B A22B Thinking",
            modalities=m,
            features=f,
        )
    )
    m, f = v(vision=True)
    out.append(
        _mk_spec(
            "qwen/qwen3-vl-235b-a22b-instruct",
            label="Qwen3 VL 235B A22B Instruct",
            modalities=m,
            features=f,
        )
    )

    # anthropic
    m, f = v()
    out.append(_mk_spec("anthropic/claude-haiku-4.5", label="Claude Haiku 4.5", modalities=m, features=f))
    out.append(_mk_spec("anthropic/claude-sonnet-4.5", label="Claude Sonnet 4.5", modalities=m, features=f))
    out.append(_mk_spec("anthropic/claude-opus-4.1", label="Claude Opus 4.1", modalities=m, features=f))

    # google gemini 2.5 (vision)
    m, f = v(vision=True)
    out.append(_mk_spec("google/gemini-2.5-flash-lite", label="Gemini 2.5 Flash Lite", modalities=m, features=f))
    out.append(_mk_spec("google/gemini-2.5-flash", label="Gemini 2.5 Flash", modalities=m, features=f))
    out.append(_mk_spec("google/gemini-2.5-pro", label="Gemini 2.5 Pro", modalities=m, features=f))

    # xAI Grok (assume multimodal)
    m, f = v(vision=True)
    out.append(_mk_spec("x-ai/grok-4", label="Grok 4", modalities=m, features=f))

    # openai gpt-5 family (assume multimodal) — after Grok
    m, f = v(vision=True)
    out.append(_mk_spec("openai/gpt-5-mini", label="GPT-5 Mini", modalities=m, features=f))
    out.append(_mk_spec("openai/gpt-5", label="GPT-5", modalities=m, features=f))
    out.append(_mk_spec("openai/gpt-5-pro", label="GPT-5 Pro", modalities=m, features=f))

    # Attach pricing_source hint
    for spec in out:
        pr = spec.get("pricing") or {}
        if "pricing_source" not in pr:
            pr.update(now_src)
        spec["pricing"] = pr  # type: ignore

    return out


def validate_catalog(cat: Catalog) -> None:
    if not isinstance(cat, list):
        raise ValidationError("Catalog must be a list")
    for i, m in enumerate(cat):
        mid = m.get("id")
        if not mid or not isinstance(mid, str):
            raise ValidationError(f"Model at index {i} missing valid 'id'")
        m.setdefault("provider", _provider_from_id(mid))
        m.setdefault("label", mid)
        m.setdefault("family", _family_from_id(mid))
        m.setdefault("context_window", 128_000)
        m.setdefault("max_output_tokens", 8_192)
        mods = m.get("modalities") or {}
        m["modalities"] = {
            "text": _bool(mods.get("text")),
            "vision": _bool(mods.get("vision")),
            "audio_in": _bool(mods.get("audio_in")),
            "audio_out": _bool(mods.get("audio_out")),
        }
        feats = m.get("features") or {}
        m["features"] = {
            "json_mode": _bool(feats.get("json_mode", True)),
            "tool_use": _bool(feats.get("tool_use", True)),
            "function_call": _bool(feats.get("function_call", True)),
            "reasoning": _bool(feats.get("reasoning")),
        }
        tiers = m.get("tiers") or {}
        q = tiers.get("quality", "mid")
        if q not in ("low", "mid", "high"):
            q = "mid"
        s = tiers.get("speed", "balanced")
        if s not in ("fast", "balanced", "slow"):
            s = "balanced"
        m["tiers"] = {"quality": q, "speed": s}
        pr = m.get("pricing") or {}
        if pr:
            if v := pr.get("input_per_million"):
                if float(v) < 0:
                    raise ValidationError("pricing.input_per_million must be >= 0")
            if v := pr.get("output_per_million"):
                if float(v) < 0:
                    raise ValidationError("pricing.output_per_million must be >= 0")
            pr.setdefault("currency", "USD")
        m["pricing"] = pr
        lim = m.get("limits") or {}
        if "tpm" in lim and int(lim["tpm"]) < 0:
            raise ValidationError("limits.tpm must be >= 0")
        if "rpm" in lim and int(lim["rpm"]) < 0:
            raise ValidationError("limits.rpm must be >= 0")
        m["limits"] = lim


def _deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(a)
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def merge_catalogs(
    base: Catalog,
    overrides: Catalog,
    *,
    on_conflict: Literal["prefer_overrides", "prefer_base"] = "prefer_overrides",
) -> Catalog:
    idx: Dict[str, ModelSpec] = {m["id"]: dict(m) for m in base if m.get("id")}
    for m in overrides:
        mid = m.get("id")
        if not mid:
            continue
        if mid in idx:
            if on_conflict == "prefer_overrides":
                idx[mid] = _deep_merge(idx[mid], m)  # type: ignore
            else:
                idx[mid] = _deep_merge(m, idx[mid])  # type: ignore
        else:
            idx[mid] = dict(m)
    out = list(idx.values())
    validate_catalog(out)
    return out


def select_model(
    cat: Catalog,
    *,
    task: Literal["chat", "reason", "vision", "json", "tool"],
    budget: Literal["low", "mid", "high"] = "mid",
    prefer: Optional[List[str]] = None,
) -> ModelSpec:
    validate_catalog(cat)
    prefer = prefer or []

    def ok(m: ModelSpec) -> bool:
        mods = m.get("modalities", {})
        feats = m.get("features", {})
        if task == "vision":
            return bool(mods.get("vision"))
        if task == "json":
            return bool(feats.get("json_mode", True))
        if task == "tool":
            return bool(feats.get("tool_use", True) or feats.get("function_call", True))
        if task == "reason":
            return bool(feats.get("reasoning"))
        return bool(mods.get("text", True))

    allowed_csv = os.getenv("OPENROUTER_ALLOWED_MODELS", "").strip()
    allowed: Optional[set[str]] = None
    if allowed_csv:
        allowed = {x.strip() for x in allowed_csv.split(",") if x.strip()}

    pool = [m for m in cat if ok(m) and ((allowed is None) or (m["id"] in allowed))]
    if not pool:
        raise ValidationError("No models match the selection criteria")

    # Prefer explicit ids first
    for p in prefer:
        for m in pool:
            if m["id"] == p:
                return m

    # Rank by (budget ~ tiers.quality), then speed
    quality_rank = {"low": 0, "mid": 1, "high": 2}
    speed_rank = {"fast": 2, "balanced": 1, "slow": 0}

    def key(m: ModelSpec):
        t = m.get("tiers", {})
        q = t.get("quality", "mid")
        s = t.get("speed", "balanced")
        # Adjust target quality to budget preference
        target = {"low": 0, "mid": 1, "high": 2}[budget]
        qv = quality_rank.get(q, 1)
        # closeness to target quality; smaller is better
        qscore = -abs(qv - target)
        return (qscore, speed_rank.get(s, 1))

    pool.sort(key=key, reverse=True)
    return pool[0]


def export_catalog(cat: Catalog, *, format: Literal["json", "dict"] = "json") -> str | List[Dict[str, Any]]:
    validate_catalog(cat)
    if format == "json":
        return json.dumps(cat, ensure_ascii=False, indent=2)
    return json.loads(json.dumps(cat))


def ensure_models(upserter: Callable[[ModelSpec], None], cat: Catalog | None = None) -> None:
    data = cat or get_default_catalog()
    validate_catalog(data)
    for m in data:
        upserter(m)


def resolve_model_id(alias_or_id: str, cat: Catalog | None = None) -> str:
    cat = cat or get_default_catalog()
    for m in cat:
        if m.get("id") == alias_or_id:
            return alias_or_id
        if m.get("label", "").lower() == alias_or_id.lower():
            return m["id"]
    return alias_or_id


def fetch_openrouter_models(ttl: int = 3600) -> Catalog:
    now = time.time()
    if _CACHE["data"] and (now - _CACHE["ts"]) < _CACHE["ttl"]:
        return _CACHE["data"]  # type: ignore

    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set.")

    with httpx.Client(timeout=20) as client:
        r = client.get(_MODELS_ENDPOINT, headers=_or_headers())
        r.raise_for_status()
        raw = r.json()

    items = raw.get("data") if isinstance(raw, dict) else raw
    cat: Catalog = []
    if isinstance(items, list):
        for it in items:
            mid = it.get("id") if isinstance(it, dict) else None
            if not mid:
                continue
            label = it.get("name") or mid
            ctx = it.get("context_length") or it.get("context_length_tokens") or 128_000
            # basic mapping; many fields are not standardized across vendors
            cat.append(
                _mk_spec(
                    mid,
                    label=label,
                    context_window=int(ctx) if isinstance(ctx, int) else 128_000,
                    modalities=_default_modalities(vision=False),
                    features=_default_features(),
                    pricing={"currency": "USD", "pricing_source": "openrouter-list"},
                )
            )

    validate_catalog(cat)
    _CACHE.update({"ts": now, "ttl": int(ttl), "data": cat})
    return cat
