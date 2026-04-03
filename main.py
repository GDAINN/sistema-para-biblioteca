from fastapi import FastAPI, HTTPException

app = FastAPI()

meu_dicionario = {}

@app.get("/livros")
def get_livros():
    if not meu_dicionario:
        return {"message": "Nenhum livro encontrado."}
    else:
        return{"livros": meu_dicionario}

@app.post("/adicionar")
def post_livros(id: int, titulo: str, autor: str, ano: int):
    if id in meu_dicionario:
        raise HTTPException(status_code=400,detail="Esse livro já existe.")
    else:
        meu_dicionario[id] = {"nome": titulo, "autor": autor, "ano": ano}
        return {"message": "Livro foi criado"}
    
@app.put("/atualizar/{id}")
def put_livros(id: int, titulo: str, autor: str, ano: int):
    meu_livros = meu_dicionario.get(id)
    if not meu_livros:
        raise HTTPException(status_code=404, detail="Livro não encontrado.")
    else:
        if titulo:
            meu_livros["nome"] = titulo
        if autor:
            meu_livros["autor"] = autor
        if ano:
            meu_livros["ano"] = ano
        
        return {"message": "Livro atualizado com sucesso."}

@app.delete("/deletar/{id}")
def delete_livros(id: int):
    if id not in meu_dicionario:
        raise HTTPException(status_code=404, detail="Livro não encontrado.")
    else:
        del meu_dicionario[id]
        return {"message": "Livro deletado com sucesso."}
