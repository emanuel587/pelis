from pathlib import Path
import html as html_lib
import json
import re

import requests

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

SOURCES_FILE = BASE_DIR / "remote_sources.json"


# ============================================================
# TMDB
# ============================================================
#
# PEGA AQUÍ TU API KEY CORTA DE TMDB.
#
# Ejemplo:
#
# TMDB_API_KEY = "1234567890abcdef..."
#
# NO pongas aquí el Bearer largo.
# ============================================================

TMDB_API_KEY = "PEGA_AQUI_TU_API_KEY"


TMDB_API = "https://api.themoviedb.org/3"


# ============================================================
# HEADERS PARA COMPROBAR EMBED69
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),

    "Accept": (
        "text/html,"
        "application/xhtml+xml,"
        "application/xml;q=0.9,"
        "*/*;q=0.8"
    ),

    "Accept-Language":
        "es-MX,es;q=0.9,en;q=0.7"
}


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Cine Latino API",
    version="4.0"
)


app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=False,

    allow_methods=["*"],

    allow_headers=["*"]
)


# ============================================================
# INDEX.HTML
# ============================================================

@app.get("/")
def inicio():

    archivo = BASE_DIR / "index.html"

    if not archivo.exists():

        raise HTTPException(
            status_code=404,
            detail="No existe index.html"
        )

    return FileResponse(
        archivo
    )


# ============================================================
# TMDB
# ============================================================

def tmdb_request(
    endpoint: str,
    params: dict | None = None
):

    if (
        not TMDB_API_KEY
        or
        "PEGA_AQUI" in TMDB_API_KEY
    ):

        raise HTTPException(
            status_code=500,
            detail=(
                "Falta poner tu API Key "
                "de TMDB en api.py"
            )
        )


    final_params = {

        "api_key":
            TMDB_API_KEY,

        "language":
            "es-MX",

        "region":
            "MX"
    }


    if params:

        final_params.update(
            params
        )


    try:

        response = requests.get(

            TMDB_API + endpoint,

            params=final_params,

            timeout=15
        )

    except requests.RequestException as error:

        raise HTTPException(
            status_code=502,
            detail=(
                "No se pudo conectar "
                f"con TMDB: {error}"
            )
        )


    try:

        data = response.json()

    except ValueError:

        raise HTTPException(
            status_code=502,
            detail=(
                "TMDB devolvió "
                "una respuesta inválida"
            )
        )


    if not response.ok:

        raise HTTPException(
            status_code=response.status_code,
            detail=data.get(
                "status_message",
                "Error de TMDB"
            )
        )


    return data


# ============================================================
# CATÁLOGO TMDB
# ============================================================

@app.get("/api/movies")
def peliculas(
    page: int = Query(
        1,
        ge=1,
        le=500
    ),

    sort: str =
        "popularity.desc"
):

    permitidos = {

        "popularity.desc",

        "primary_release_date.desc",

        "vote_average.desc"
    }


    if sort not in permitidos:

        sort = "popularity.desc"


    params = {

        "page":
            page,

        "sort_by":
            sort,

        "include_adult":
            "false"
    }


    if (
        sort ==
        "vote_average.desc"
    ):

        params[
            "vote_count.gte"
        ] = 200


    return tmdb_request(
        "/discover/movie",
        params
    )


# ============================================================
# BUSCADOR TMDB
# ============================================================

@app.get("/api/search")
def buscar(
    q: str,

    page: int = Query(
        1,
        ge=1,
        le=500
    )
):

    q = q.strip()


    if not q:

        raise HTTPException(
            status_code=400,
            detail=(
                "Escribe el nombre "
                "de una película"
            )
        )


    return tmdb_request(
        "/search/movie",

        {
            "query":
                q,

            "page":
                page,

            "include_adult":
                "false"
        }
    )


# ============================================================
# DETALLE TMDB + IMDb
# ============================================================

@app.get("/api/movie/{tmdb_id}")
def pelicula(
    tmdb_id: int
):

    return tmdb_request(

        f"/movie/{tmdb_id}",

        {
            "append_to_response":
                "external_ids,videos"
        }
    )


# ============================================================
# UTILIDADES EMBED69
# ============================================================

def limpiar_html(
    contenido: str
):

    contenido = re.sub(

        r"<script\b[^>]*>.*?</script>",

        " ",

        contenido,

        flags=re.I | re.S
    )


    contenido = re.sub(

        r"<style\b[^>]*>.*?</style>",

        " ",

        contenido,

        flags=re.I | re.S
    )


    contenido = re.sub(

        r"<[^>]+>",

        " ",

        contenido
    )


    contenido = html_lib.unescape(
        contenido
    )


    contenido = re.sub(

        r"\s+",

        " ",

        contenido
    )


    return contenido.strip()


def obtener_titulo_embed69(
    contenido: str
):

    texto = limpiar_html(
        contenido
    )


    match = re.search(

        r"Est[aá]s\s+viendo\s*:\s*(.*?)"
        r"(?=\s+(?:LAT|ESP|SUB|ENG|JAP)\b"
        r"|\s+\d+\s+Servidores"
        r"|$)",

        texto,

        re.I
    )


    if match:

        titulo = (
            match
            .group(1)
            .strip()
        )


        if titulo:

            return titulo


    match = re.search(

        r"<title[^>]*>(.*?)</title>",

        contenido,

        re.I | re.S
    )


    if match:

        titulo = limpiar_html(
            match.group(1)
        )


        titulo = re.sub(

            r"\s*\|\s*EMBED69.*$",

            "",

            titulo,

            flags=re.I
        )


        return titulo.strip()


    return None


def obtener_idiomas_embed69(
    contenido: str
):

    texto = limpiar_html(
        contenido
    ).upper()


    encontrados = []


    for idioma in [

        "LAT",

        "ESP",

        "SUB",

        "ENG",

        "JAP"

    ]:

        if re.search(
            rf"\b{idioma}\b",
            texto
        ):

            encontrados.append(
                idioma
            )


    return encontrados


def obtener_servidores_embed69(
    contenido: str
):

    texto = limpiar_html(
        contenido
    )


    patrones = [

        r"(\d+)\s+Servidores",

        r"(\d+)\s+Servidor",

        r"Servidores\s*:\s*(\d+)"
    ]


    for patron in patrones:

        match = re.search(

            patron,

            texto,

            re.I
        )


        if match:

            return int(
                match.group(1)
            )


    return None


# ============================================================
# COMPROBAR EMBED69
# ============================================================

@app.get(
    "/api/embed69/{imdb_id}"
)
def comprobar_embed69(
    imdb_id: str
):

    imdb_id = (
        imdb_id
        .strip()
        .lower()
    )


    if not re.fullmatch(
        r"tt\d{5,12}",
        imdb_id
    ):

        raise HTTPException(
            status_code=400,
            detail="IMDb ID inválido"
        )


    url = (
        "https://embed69.org/f/"
        f"{imdb_id}/"
    )


    try:

        response = requests.get(

            url,

            headers=HEADERS,

            timeout=15,

            allow_redirects=True
        )

    except requests.RequestException as error:

        raise HTTPException(
            status_code=502,
            detail=(
                "No se pudo consultar "
                f"Embed69: {error}"
            )
        )


    contenido = response.text


    titulo = obtener_titulo_embed69(
        contenido
    )


    idiomas = obtener_idiomas_embed69(
        contenido
    )


    servidores = obtener_servidores_embed69(
        contenido
    )


    texto = limpiar_html(
        contenido
    ).lower()


    disponible = (

        response.status_code == 200

        and

        (

            titulo is not None

            or

            servidores is not None

            or

            "estás viendo" in texto

            or

            "estas viendo" in texto
        )
    )


    return {

        "estado":

            "disponible"

            if disponible

            else "no_disponible",


        "imdb_id":
            imdb_id,


        "http_status":
            response.status_code,


        "titulo":
            titulo,


        "idiomas":
            idiomas,


        "servidores":
            servidores,


        "endpoint":
            url
    }


# ============================================================
# FUENTES REMOTAS
# ============================================================

def cargar_fuentes():

    if not SOURCES_FILE.exists():

        return {}


    try:

        contenido = (
            SOURCES_FILE
            .read_text(
                encoding="utf-8"
            )
        )


        data = json.loads(
            contenido
        )


        if not isinstance(
            data,
            dict
        ):

            return {}


        return data

    except Exception as error:

        print(
            "Error remote_sources.json:",
            error
        )


        return {}


# ============================================================
# BUSCAR FUENTE POR TMDB O IMDb
# ============================================================

@app.get(
    "/api/source/{tmdb_id}/{imdb_id}"
)
def fuente_remota(
    tmdb_id: int,
    imdb_id: str
):

    imdb_id = (
        imdb_id
        .strip()
        .lower()
    )


    fuentes = cargar_fuentes()


    posibles = [

        str(tmdb_id),

        imdb_id
    ]


    for identificador in posibles:

        entrada = fuentes.get(
            identificador
        )


        if not isinstance(
            entrada,
            dict
        ):

            continue


        url = str(
            entrada.get(
                "url",
                ""
            )
        ).strip()


        if not url:

            continue


        tipo = str(
            entrada.get(
                "type",
                "auto"
            )
        ).lower()


        idioma = str(
            entrada.get(
                "idioma",
                ""
            )
        )


        return {

            "disponible":
                True,

            "id":
                identificador,

            "url":
                url,

            "type":
                tipo,

            "idioma":
                idioma
        }


    return {

        "disponible":
            False,

        "tmdb_id":
            tmdb_id,

        "imdb_id":
            imdb_id
    }


# ============================================================
# TEST
# ============================================================

@app.get("/api/test")
def test():

    return {

        "estado":
            "ok",

        "mensaje":
            "API local funcionando",

        "tmdb":
            bool(
                TMDB_API_KEY
                and
                "PEGA_AQUI"
                not in TMDB_API_KEY
            ),

        "sources_file":
            str(
                SOURCES_FILE
            )
    }