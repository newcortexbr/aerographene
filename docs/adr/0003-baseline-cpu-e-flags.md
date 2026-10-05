# baseline x86-64-v3 e flags de build da v1

O binário principal mira x86-64-v3 (AVX2, FMA, BMI2), que é o ótimo para as máquinas principais (Comet Lake U e Cezanne). A Ivy Bridge fica sem build até existir um segundo alvo v2+AVX, previsto para quando o CI estiver estável. Flags da v1: ThinLTO, ICF, `symbol_level=0`, PGO com o perfil oficial do Chromium (se o ungoogled permitir) e `-march=x86-64-v3`. `-O3` não entra de saída: ele aumenta o binário e pode piorar a abertura, então só entra se medido contra `-O2`, uma mudança por vez.
