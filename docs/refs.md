# Referências

## Datasets usados

| Dataset | Uso no projeto | Licença |
| --- | --- | --- |
| [Dataset-FactPolCheckBr](https://github.com/Interfaces-UFSCAR/Dataset-FactPolCheckBr) (UFSCar) | checagens de 2022; base da camada 1 e dos casos de [`data/testes_benchmark.json`](https://github.com/gpaulovit/RES-IA-Challenge-1/blob/main/data/testes_benchmark.json) | CC BY-NC-SA 4.0 |
| [FactChecks.br](https://github.com/fake-news-UFG/FactChecks.br) v0.1 (Gomes, DOI `10.57967/hf/1016`) | reúne os três abaixo; treino e teste da camada 2 | MIT (Hugging Face) |
| Central de Fatos (Couto et al., DSW 2021), via FactChecks.br | checagens de 2013 a 2021 | termos de uso a conferir antes do deploy |
| [Fake.br-Corpus](https://github.com/roneysco/Fake.br-Corpus) (Monteiro et al., PROPOR 2018), via FactChecks.br | notícias falsas e verdadeiras, com exemplos verdadeiros para a camada 2 | ver repositório |
| FakeRecogna (Garcia et al., PROPOR 2022), via FactChecks.br | notícias falsas e verdadeiras, com exemplos verdadeiros para a camada 2 | ver repositório |
| Base de checagens da frente de Dados | `data/processados/checagens/checagens.json`, unificada com vereditos normalizados (RN-02) | herda as licenças acima |

Os hashes e a procedência dos arquivos estão no [README de experiments](https://github.com/gpaulovit/RES-IA-Challenge-1/blob/main/experiments/README.md).

### Avaliados e não usados

- [FakeNewsNet](https://github.com/KaiDMML/FakeNewsNet): em inglês.
- [FakeTweet.Br](https://github.com/prc992/FakeTweet.Br), [BRACIS2019_FAKENEWS](https://github.com/phfaustini/BRACIS2019_FAKENEWS) e [FACTCK.BR](https://github.com/jghm-f/FACTCK.BR): não entraram no MVP.

## MLOps

- Kreuzberger, D., Kühl, N., & Hirschl, S. (2023). *Machine Learning Operations (MLOps): Overview, Definition, and Architecture*. IEEE Access, 11, 31866–31879. [doi:10.1109/ACCESS.2023.3262138](https://doi.org/10.1109/ACCESS.2023.3262138)
- [DVC](https://dvc.org): versionamento de dados, modelo e métricas.

## SDD

- [spec-kit](https://github.github.com/spec-kit/)
- [OpenSpec](https://openspec.dev)
