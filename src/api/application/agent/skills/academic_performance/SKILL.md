---
name: academic_performance
description: Notas, AVs, média, frequência, aprovação, reprovação, coeficiente e conclusão do curso. Carregue para perguntas sobre desempenho nas disciplinas.
---

# Desempenho

- Use `list_subject_records` para notas, frequência e resultado, filtrando pelo semestre quando a pergunta for sobre o atual. Quem repetiu tem várias linhas da mesma disciplina: diga de qual semestre fala.
- Nome de disciplina pode ser ambíguo. Com status `ambiguous`, mostre as opções ou responda sobre todas as que couberem.
- Nota vazia não é zero: diga que ainda não aconteceu ou que não foi registrada, conforme o campo. O mesmo vale para frequência não registrada.
- O critério de aprovação e o limite de frequência são deduzidos dos dados, não de um regulamento. Ao calcular a nota necessária, avise sempre que é uma estimativa e sugira confirmar com o professor.
- Em reprovação, diferencie reprovação por nota de reprovação por frequência.
- Um registro estranho, como reprovação antes do fim do semestre, é mostrado como está, sem confirmar nem descartar, com a sugestão de verificar na secretaria.
- `list_enrollments` traz o coeficiente, que é por matrícula. Use `get_curriculum` para o que falta para a conclusão.
