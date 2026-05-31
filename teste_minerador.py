from trabalho_pratico_grafos.minerador import Minerador

minerador = Minerador("folke/ultra-runner", "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")
minerador.executar(0.2)

print(str(minerador.quantidadeUsuarios()) + " Usuários")
print(str(minerador.quantidadeInteracoes()) + " Interações")
print(minerador.verInteracoes())