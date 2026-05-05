"""
Bibliotecas externas usadas no projeto.

Arquivo auxiliar solicitado para listar dependencias.
"""

REQUERIMENTOS = [
    "numpy",
    "pandas",
    "faker",
    "tqdm",
]


if __name__ == "__main__":
    print("Bibliotecas necessarias:")
    for lib in REQUERIMENTOS:
        print(f"- {lib}")
