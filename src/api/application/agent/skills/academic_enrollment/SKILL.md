---
name: academic_enrollment
description: Vínculo do aluno, matrícula, rematrícula, trancamento, matriz, pré-requisitos, TCC, estágio, cursos oferecidos e calendário. Carregue para perguntas sobre o curso e a situação da matrícula.
---

# Vínculo e curso

- Use `list_enrollments` para a situação da matrícula e `get_academic_calendar` para o semestre atual e as datas.
- A mesma pessoa pode ter mais de uma matrícula: cubra todas na resposta, ou pergunte de qual ela fala quando isso muda a resposta.
- Para o que falta cursar, pré-requisitos, TCC e estágio, use `get_curriculum`. Vale a matriz do aluno, não a mais nova. Só chame de TCC o que estiver registrado assim.
- Com `show_ui`, `get_curriculum` mostra ao aluno um anel com o percentual concluído do curso, as horas e as disciplinas que faltam. Ligue só quando a pergunta do aluno é sobre esse resultado, no máximo uma vez por resposta, e responda em texto completo do mesmo jeito.
- Para saber se um curso, modalidade ou turno existe, use `list_course_offers`. A resposta fica restrita à instituição do aluno, e vagas não estão nos dados.
- O calendário traz o início dos períodos, não a data da prova de cada disciplina. Não existe calendário depois do último semestre cadastrado.
- Regras de prazo e limite de trancamento não estão nos dados. O histórico mostra o que aconteceu, não a regra.
