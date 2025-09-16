from functools import lru_cache
import numpy as np
import html
from bs4 import BeautifulSoup
from bs4 import MarkupResemblesLocatorWarning
from ftfy import fix_text
import re
import unicodedata
from sklearn.base import BaseEstimator, TransformerMixin
import pandas as pd
from tqdm import tqdm

import json
from langdetect import detect_langs
import fasttext

import pickle
import hashlib
import os

import torch

import gc
import warnings

from sklearn.pipeline import Pipeline

from api.config.config import get_settings
from api.config.dependencies import get_french_words

tqdm.pandas()

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

##### Variables  and constants #####

# key words for clean_text (delete complete line)
key_words_to_delete = [r"\battention\s*!{3}\b"]

# french words to detect and force FR language
FRENCH_HINTS = {
    "buste",
    "livre",
    "voiture",
    "figurine",
    "jouet",
    "camion",
    "collection",
    "édition",
    "tome",
    "modèle",
    "poster",
    "peluche",
    "coffret",
    "volume",
    "magazine",
    "import",
    "carte",
    "livres",
    "revue",
    "jeu",
    "volumes",
    "jeux",
    "tomes",
    "magazines",
    "revues",
    "manette",
    "manettes",
    "maquette",
}

# EU languages
EU_LANGS = {"de", "fr", "en", "es", "it", "pt", "nl", "sv", "ca", "pl", "cs"}

# translation correspondences
LANG_CODE_MAP = {
    "ca": "cat_Latn",
    "cs": "ces_Latn",
    "de": "deu_Latn",
    "en": "eng_Latn",
    "es": "spa_Latn",
    "fr": "fra_Latn",
    "it": "ita_Latn",
    "nl": "nld_Latn",
    "pl": "pol_Latn",
    "pt": "por_Latn",
    "sv": "swe_Latn",
}

TARGET_LANGUAGE = "eng_Latn"
SOURCE_LANGUAGES = [
    "fra_Latn",
    "cat_Latn",
    "ces_Latn",
    "deu_Latn",
    "spa_Latn",
    "ita_Latn",
    "nld_Latn",
    "pol_Latn",
    "por_Latn",
    "swe_Latn",
]

ENCODER_CATEGORIES = {
    0: 10,
    1: 40,
    2: 50,
    3: 60,
    4: 1140,
    5: 1160,
    6: 1180,
    7: 1280,
    8: 1281,
    9: 1300,
    10: 1301,
    11: 1302,
    12: 1320,
    13: 1560,
    14: 1920,
    15: 1940,
    16: 2060,
    17: 2220,
    18: 2280,
    19: 2403,
    20: 2462,
    21: 2522,
    22: 2582,
    23: 2583,
    24: 2585,
    25: 2705,
    26: 2905,
}

DEFAULT_BATCH_SIZE = 8
MIN_BATCH_SIZE = 1
CACHE_FILE = "data/translation_cache_english.pkl"

# %%

##### Functions #####


def clean_text_basic(texte):
    """
    Deleting by keywords, HTML balises and correcting bad syntaxes,...
    for detecting language

    Args:
        text (str): text to clean
    Return:
        text cleaned
    """
    if not isinstance(texte, str):
        return texte
    # clean invisible characters
    texte = re.sub(r"[\r\n\t\x0b\x0c\x0e-\x1f\u200b\u200e\u200f]", " ", texte)
    #  delete 'br' alone or paste to word
    texte = re.sub(r"([a-zA-Z])br\b", r"\1 ", texte, flags=re.IGNORECASE)
    texte = re.sub(r"\bbr([a-zA-Z])", r" \1", texte, flags=re.IGNORECASE)
    texte = re.sub(r"\bbr\b", " ", texte, flags=re.IGNORECASE)
    texte = re.sub(r"br", " ", texte, flags=re.IGNORECASE)
    # delete spave in HTML balises
    texte = re.sub(r"<\s*br\s*/?\s*>|[\s\-]br[\s\-]", " ", texte, flags=re.IGNORECASE)
    # correct HTML balises
    texte = re.sub(r"<[^>]+>", " ", texte)
    # replace '_' by ' '
    texte = re.sub(r"_+", " ", texte)
    # decode HTML entities
    texte = html.unescape(texte)
    # delete HTML balises
    texte = BeautifulSoup(texte, "html.parser").get_text(separator=" ", strip=True)
    # delete key_words_to_delete (complete line)
    for pattern in key_words_to_delete:
        if re.search(pattern, texte, flags=re.IGNORECASE):
            return np.nan
    # correction bad syntax
    texte = fix_text(texte)
    # word separation
    texte = re.sub(r"([a-z])([A-Z])", r"\1 \2", texte)
    # delete multiple spaces
    texte = re.sub(r"\s{2,}", " ", texte).strip()
    # delete specific carachters
    texte = re.sub(r"[^\w\s\.,:;()\[\]\'\"/-]", "", texte)
    return texte


def clean_text_full(texte):
    """
    Deleting by keywords, HTML balises and correcting bad syntaxes,...
    for detecting language

    Args:
        text (str): text to clean
    Return:
        text cleaned
    """
    raw_text = texte
    # delete " " in HTML
    texte = re.sub(r"<\s*/?\s*([^>]+?)\s*>", r"<\1>", texte)
    # replace underscores by space
    texte = re.sub(r"_+", " ", texte)
    # decode HTML entities
    texte = html.unescape(texte)
    # delete HTML balises
    texte = BeautifulSoup(texte, "html.parser").get_text(separator=" ", strip=True)
    # delete by searching key_words
    for pattern in key_words_to_delete:
        if re.search(pattern, texte, flags=re.IGNORECASE):
            return np.nan
    # bad characters correction
    texte = fix_text(texte)
    try:
        texte = texte.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    # normalization Unicode
    texte = unicodedata.normalize("NFKC", texte)
    # delete formats type
    texte = re.sub(r"\b\d{1,4}\s?[-xX/×]\s?\d{1,4}\b", " ", texte)
    # delete units
    texte = re.sub(
        r"\b\d+(\.\d+)?\s?(cm|mm|m|km|g|kg|mg|cl|ml|l|L|v|V|hz|dpi|mmHg)\b",
        " ",
        texte,
        flags=re.IGNORECASE,
    )
    # delete int
    texte = re.sub(r"\d+", " ", texte)
    # clean invisible characters
    texte = re.sub(r"[\r\n\t\x0b\x0c\x0e-\x1f\u200b\u200e\u200f]", " ", texte)
    # delete /, \ and |
    texte = re.sub(r"[\\/|]", " ", texte)
    # delete multiple spaces
    texte = re.sub(r"\s{2,}", " ", texte).strip()
    return raw_text, texte


def detect_language(text, fasttext_model):
    """
    Detect languages

    Args:
        text (str): text to detect
        fasttext_model (model instance): model loaded
        threshold_fasttext (float): fasttext threshold to be right
        threshold_agreement (float): langdetect threshold to be right
        debug (boolean): return score details if true
    Return:
        return language detected and score

    """
    threshold_fasttext = 0.45
    threshold_agreement = 0.5
    if not isinstance(text, str) or len(text.strip()) < 2:
        return ("unknown", 0.0)
    clean_text = text.replace("\n", " ").replace("\r", " ").strip()
    tokens = re.findall(r"\w+", clean_text.lower())
    text_without_duplicates = " ".join(dict.fromkeys(tokens))
    word_count = len(tokens)

    # FastText detection
    try:
        ft_labels, ft_scores = fasttext_model.predict(text_without_duplicates)
        ft_lang = ft_labels[0].replace("__label__", "")
        ft_score = ft_scores[0]
    except Exception:
        ft_lang, ft_score = "error", 0.0

    # langdetect detection
    try:
        ld_results = detect_langs(text_without_duplicates)
        if ld_results:
            ld_lang = ld_results[0].lang
            ld_score = ld_results[0].prob
        else:
            ld_lang, ld_score = "unknown", 0.0
    except Exception:
        ld_lang, ld_score = "error", 0.0

    # FR heuristic
    if any(word in FRENCH_HINTS for word in tokens):
        return ("fr", 0.6)
    french_words = get_french_words(settings=get_settings())
    if french_words is None:
        raise ValueError(
            "Impossible to detect language since the french words reference was null"
        )
    fr_words_in_text = [word for word in tokens if word in french_words]
    fr_hint_count = len(fr_words_in_text)
    hint_ratio = fr_hint_count / word_count if word_count else 0
    if fr_hint_count >= 3 and hint_ratio > 0.4:
        return ("fr", 0.53)

    # direct results
    if ft_score >= threshold_fasttext and ft_lang in EU_LANGS:
        return (ft_lang, ft_score)
    if ft_lang == ld_lang and ld_score >= threshold_agreement:
        mean_score = (ft_score + ld_score) / 2
        return (ft_lang, mean_score)
    else:
        return ("fr", 0.0)


# Hash cache
def make_translation_hash(text, src_lang, tgt_lang, temperature=None, model_id=None):
    base = f"{src_lang}|{tgt_lang}|{text.strip().lower()}"
    if temperature is not None:
        base += f"|temp={temperature}"
    if model_id:
        base += f"|model={model_id}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def get_cached_translation(cache, hash_key, default=None):
    return cache.get(hash_key, default)


def cache_translation(cache, hash_key, translation):
    cache[hash_key] = translation


# split text
def split_text_by_tokens(text, tokenizer, max_tokens=512):
    words = text.split()
    chunks = []
    current_chunk = []
    for word in words:
        test_chunk = current_chunk + [word]
        nb_tokens = len(
            tokenizer.encode(" ".join(test_chunk), add_special_tokens=False)
        )
        if nb_tokens > max_tokens:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            current_chunk = [word]
        else:
            current_chunk = test_chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks


# batch translation
def batch_translate_texts(
    texts,
    src_lang_code,
    tgt_lang_code,
    tokenizer,
    model,
    device,
    max_length=256,
    num_beams=4,
    batch_size=8,
):
    results = []
    if not texts:
        return results

    torch.cuda.empty_cache()
    gc.collect()
    tokenizer.src_lang = src_lang_code

    for i in range(0, len(texts), batch_size):
        sub_texts = texts[i : i + batch_size]
        if not sub_texts:
            continue

        try:
            sub_texts_truncated = [
                " ".join(text.split()[:512]) if isinstance(text, str) else ""
                for text in sub_texts
            ]

            inputs = tokenizer(
                sub_texts_truncated,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            )
            inputs = {k: v.to(device) for k, v in inputs.items()}
            forced_id = tokenizer.convert_tokens_to_ids(tgt_lang_code)

            with torch.no_grad():
                translated_tokens = model.generate(
                    **inputs,
                    forced_bos_token_id=forced_id,
                    max_length=max_length,
                    num_beams=num_beams,
                    no_repeat_ngram_size=3,
                    do_sample=False,
                )
            results.extend(
                tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)
            )
            del inputs, translated_tokens

        except Exception as e:
            # print(f"[ERROR] Batch {i} failed: {e}. Retrying line by line.")
            for txt in sub_texts:
                try:
                    txt_trunc = (
                        " ".join(txt.split()[:512]) if isinstance(txt, str) else ""
                    )
                    input = tokenizer(
                        txt_trunc,
                        return_tensors="pt",
                        padding=True,
                        truncation=True,
                        max_length=512,
                    )
                    input = {k: v.to(device) for k, v in input.items()}
                    with torch.no_grad():
                        translated_token = model.generate(
                            **input,
                            forced_bos_token_id=forced_id,
                            max_length=max_length,
                            num_beams=num_beams,
                            no_repeat_ngram_size=3,
                            do_sample=False,
                        )
                    results.append(
                        tokenizer.decode(translated_token[0], skip_special_tokens=True)
                    )
                    del input, translated_token
                except Exception as e2:
                    results.append(f"TRADUCTION_ERROR: {e2}")

        torch.cuda.empty_cache()
        gc.collect()
        # log_mem(prefix=f"[batch {i}] ")

    return results


# translate
def translate_dataframe_with_cache(
    translated_df,
    model,
    tokenizer,
    device,
    source_languages,
    tgt_lang_code,
    cache,
    chunk_max_tokens=512,
    batch_size=8,
):
    for language in source_languages:
        # print(f"Process forlang : {language}...")
        mask = (translated_df["src_languages"] == language) & translated_df[
            "basic_cleaned_text"
        ].notna()
        texts = translated_df.loc[mask, "basic_cleaned_text"]
        index_masked = texts.index

        # split long texts
        chunk_map = {}
        for idx, text in texts.items():
            if not isinstance(text, str) or not text.strip():
                chunk_map[idx] = []
                continue
            tokens = tokenizer.encode(text, add_special_tokens=False)
            if len(tokens) > chunk_max_tokens:
                chunks = split_text_by_tokens(text, tokenizer, chunk_max_tokens)
            else:
                chunks = [text]
            chunk_map[idx] = chunks

        # cache & batch
        translation_cache_map = {}
        batch_chunks = []
        batch_chunk_keys = []
        for idx, chunks in chunk_map.items():
            translation_cache_map[idx] = [None] * len(chunks)
            for chunk_idx, chunk in enumerate(chunks):
                hash_key = make_translation_hash(chunk, language, tgt_lang_code)
                cached = get_cached_translation(cache, hash_key)
                if cached:
                    translation_cache_map[idx][chunk_idx] = cached
                else:
                    batch_chunks.append(chunk)
                    batch_chunk_keys.append((hash_key, idx, chunk_idx))

        # print(f" - {len(batch_chunks)} chunks to translate {len(index_masked)} lines ({language})")

        for i in range(0, len(batch_chunks), batch_size):
            sub_chunks = batch_chunks[i : i + batch_size]
            sub_keys = batch_chunk_keys[i : i + batch_size]
            batch_translations = batch_translate_texts(
                sub_chunks,
                language,
                tgt_lang_code,
                tokenizer,
                model,
                device,
                batch_size=batch_size,
            )
            for trans, (hash_key, idx, chunk_idx) in zip(batch_translations, sub_keys):
                cache_translation(cache, hash_key, trans)
                translation_cache_map[idx][chunk_idx] = trans

            torch.cuda.empty_cache()
            gc.collect()
            # log_mem(prefix=f"[{language} batch {i}] ")

        translated_texts = []
        idx_list = []
        for idx in index_masked:
            translations = translation_cache_map.get(idx, [])
            full_translation = " ".join([t for t in translations if t])
            translated_texts.append(full_translation if full_translation else None)
            idx_list.append(idx)

        translated_series = pd.Series(translated_texts, index=idx_list)
        translated_df.loc[translated_series.index, "translation"] = translated_series

        torch.cuda.empty_cache()
        gc.collect()
        # log_mem(prefix=f"[{language} end] ")

    # Clean up
    del model, tokenizer
    torch.cuda.empty_cache()
    gc.collect()
    # log_mem(prefix="[end] ")
    return translated_df


### Pipeline ###
def get_prepocess_pipeline(
    language_detector, translator_model, translator_tokenizer, device
):
    # preprocess pipeline
    return Pipeline(
        [
            ("full_cleaning", TextCleanerFull()),
            (
                "lang_detect",
                LanguageDetector(
                    text_col="full_cleaned_text", fasttext_model=language_detector
                ),
            ),
            ("basic_cleaning", TextCleanerBasic(text_col="raw_text")),
            (
                "translation",
                Translator(
                    model=translator_model,
                    tokenizer=translator_tokenizer,
                    device=device,
                ),
            ),
        ]
    )


def full_process_english(
    df, language_detector, translator_model, translator_tokenizer, device
):
    """
    preprocessing pipeline :
    - full cleaning
    - detect languages
    - basic cleaning
    - translation in english
    """

    def _find_en(row):
        if row["src_languages"] == "eng_Latn":
            return row["basic_cleaned_text"]
        else:
            return row["translation"]

    # merge text cols
    text_merged = (
        df["designation"].fillna("").astype(str).str.strip()
        + " "
        + df["description"].fillna("").astype(str).str.strip()
    )
    # delete '\n'
    text_merged = text_merged.str.replace(r"\s+", " ", regex=True).str.strip()

    preprocess_pipeline = get_prepocess_pipeline(
        language_detector=language_detector,
        translator_model=translator_model,
        translator_tokenizer=translator_tokenizer,
        device=device,
    )

    translated_df = preprocess_pipeline.fit_transform(
        pd.DataFrame({"text": text_merged})
    )

    en_serie = translated_df.apply(_find_en, axis=1)
    df_en = pd.DataFrame({"text": en_serie})
    return df_en


@lru_cache
def get_device():
    return "cuda" if torch.cuda.is_available() else "cpu"


def inference(
    df,
    language_detector,
    text_classifier,
    text_tokenizer,
    translator_model,
    translator_tokenizer,
):
    device = get_device()
    #  TODO: See if we need to do -> translator_model = translator_model.to(device)
    df_en = full_process_english(
        df=df,
        language_detector=language_detector,
        translator_model=translator_model,
        translator_tokenizer=translator_tokenizer,
        device=device,
    )
    clf = InferenceClassifier(
        model=text_classifier, tokenizer=text_tokenizer, device=device
    )
    clf.fit(df_en)
    df_pred = clf.transform(df_en)
    clf.cleanup()
    return df_pred


# %%


### class ###
class TextCleanerFull(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        series = X["text"]
        # print("Full cleaning step :")
        df_cleaned = series.progress_apply(
            lambda x: (
                pd.Series(clean_text_full(x))
                if isinstance(x, str)
                else pd.Series([x, x])
            )
        )
        df_cleaned.columns = ["raw_text", "full_cleaned_text"]
        return df_cleaned


class LanguageDetector(BaseEstimator, TransformerMixin):
    def __init__(self, fasttext_model, text_col="full_cleaned_text"):
        self.fasttext_model = fasttext_model
        self.text_col = text_col

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        if "raw_text" not in X.columns:
            raise ValueError("Column 'raw_text' doesn't exist.")
        text_series = X[self.text_col]
        # print("Language detection step :")
        languages = text_series.progress_apply(
            lambda x: detect_language(x, self.fasttext_model)
        )
        df_lang = pd.DataFrame(
            languages.tolist(), columns=["src_languages", "score"]
        ).reset_index(drop=True)
        df_raw = X[["raw_text"]].reset_index(drop=True)
        return pd.concat([df_raw, df_lang], axis=1)


class TextCleanerBasic(BaseEstimator, TransformerMixin):
    def __init__(self, text_col="raw_text"):
        self.text_col = text_col

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        # print("Basic cleaning step :")
        cleaned = X[self.text_col].progress_apply(
            lambda x: clean_text_basic(x) if isinstance(x, str) else x
        )
        return pd.DataFrame(
            {
                "basic_cleaned_text": cleaned,
                "src_languages": X["src_languages"],
                "score": X["score"],
            }
        )


class Translator(BaseEstimator, TransformerMixin):
    def __init__(
        self,
        model,
        tokenizer,
        device,
        source_languages=SOURCE_LANGUAGES,
        tgt_lang_code=TARGET_LANGUAGE,
        cache=CACHE_FILE,
    ):
        self.source_languages = source_languages
        self.tgt_lang_code = tgt_lang_code
        self.cache_file = cache
        if os.path.exists(cache):
            with open(cache, "rb") as f:
                self.cache = pickle.load(f)
        else:
            self.cache = {}
        self.model = model
        self.tokenizer = tokenizer
        self.device = device

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X["src_languages"] = X["src_languages"].replace(LANG_CODE_MAP)
        df_translated = translate_dataframe_with_cache(
            X,
            model=self.model,
            tokenizer=self.tokenizer,
            device=self.device,
            source_languages=self.source_languages,
            tgt_lang_code=self.tgt_lang_code,
            cache=self.cache,
        )
        with open(self.cache_file, "wb") as f:
            pickle.dump(self.cache, f)
        return df_translated


class InferenceClassifier(BaseEstimator, TransformerMixin):
    def __init__(self, model, tokenizer, device="cpu", batch_size=32, use_gpu=True):
        self.batch_size = batch_size
        self.use_gpu = use_gpu
        self.model = model
        self.tokenizer = tokenizer
        self.device = device if use_gpu else "cpu"

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df = X.copy()
        texts = df["text"].tolist()
        preds = []
        probas_all = []
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i : i + self.batch_size]
            inputs = self.tokenizer(
                batch_texts, padding=True, truncation=True, return_tensors="pt"
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            with torch.no_grad():
                outputs = self.model(**inputs)
                probas = torch.nn.functional.softmax(outputs.logits, dim=-1)
                pred_labels = torch.argmax(probas, dim=-1).cpu().numpy()
                # pred_probs = probas[torch.arange(len(pred_labels)), pred_labels].cpu().numpy()
                preds.extend(pred_labels)
                probas_all.extend(probas.cpu().numpy().tolist())
        df["predicted_category"] = preds
        df["categories_probabilities"] = probas_all
        class_indices = [ENCODER_CATEGORIES[i] for i in range(27)]
        df["category_codes"] = [class_indices] * len(df)
        return df

    def cleanup(self):
        del self.model, self.tokenizer
        torch.cuda.empty_cache()
        gc.collect()

    def __del__(self):
        try:
            self.cleanup()
        except Exception:
            pass
