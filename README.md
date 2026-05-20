# Wide ISP Patcher

**Ferramenta para patching do binário Chromatix**  
Corrige efeito sabonete, altas luzes queimadas e sombras esmagadas no sensor.

> ✅ Executado no **Windows** — direto no PC.

---

## Dispositivo suportado

| Campo | Valor |
|---|---|
| Dispositivo | Xiaomi 11 Series |
| SoC | Snapdragon 888 |

---

## Pré-requisitos

- **Python 3.8+** instalado no Windows ([python.org](https://www.python.org/downloads/))
- Nenhuma dependência externa — usa apenas módulos da biblioteca padrão (`os`, `struct`, `zipfile`, `subprocess`, `shutil`)
- **ADB** no PATH do sistema (opcional — necessário apenas para instalar via USB)
- Módulo Magisk **PATCH_CAM.zip** pré-configurado (opcional — necessário apenas para deploy via ADB)

---

## Instalação

```
git clone https://github.com/seu-usuario/s5khm2-isp-patcher.git
cd s5khm2-isp-patcher
```

Sem `pip install` necessário.

---

## Estrutura de pastas

```
s5khm2-isp-patcher/
├── Patcher_full_V3.py       ← script principal
├── input/                   ← coloque o .bin original aqui
│   └── com_qti_tuned_vili_sunny_s5khm2_wide.bin
├── output/                  ← bin patchado gerado aqui (criado automaticamente)
│   └── PATCH_CAM.zip        ← módulo Magisk base (coloque aqui se for usar ADB)
└── README.md
```

---

## Como usar

### 1. Obter o binário original

Extraia o arquivo `.bin` do seu dispositivo via ADB:

```bat
adb pull /vendor/lib64/camera/com_qti_tuned_vili_sunny_s5khm2_wide.bin input\
```

Ou copie-o manualmente de uma ROM `xiaomi.eu` / MIUI extraída.

### 2. Executar o patcher

```bat
python Patcher_full_V3.py
```

O script detecta automaticamente o `.bin` na pasta `input/`. Se houver múltiplos arquivos, exibe um menu de seleção.

### 3. Navegar pelo menu principal

```
──────────────────────────────────────────────────────────────────────
  MENU PRINCIPAL  [com_qti_tuned_vili_sunny_s5khm2_wide.bin]
──────────────────────────────────────────────────────────────────────
  [S] Atualizar status dos módulos
  [L] Trocar arquivo .bin (carregar outra lib)
  [1] Etapa 1  — ANR Luma + Chroma        ← comece aqui
  [2] Etapa 2  — HNR + LENR
  [3] Etapa 3  — ASF Sharpening
  [4] Etapa 4  — GTM Global Tone Mapping
  [5] Etapa 5  — LTM Local Tone Mapping
  [6] Etapa 6  — TMC Tone Mapping Control
  [7] Etapa 7  — GAMMA  ⚠️  APENAS TESTE
  [8] Etapa 8  — MF Multi Frame
  [9] Etapa 9  — TF Temporal Filter/MFNR  ← mais agressivo
  [A] Aplicar TODAS as etapas (exceto Gamma)
──────────────────────────────────────────────────────────────────────
  [Z] Atualizar PATCH_CAM.zip com o bin patchado
  [I] Atualizar zip E instalar via ADB (reinicia o aparelho)
──────────────────────────────────────────────────────────────────────
```

### 4. Aplicar patches

Cada etapa possui um submenu onde você pode selecionar patches individuais ou aplicar todos de uma vez. O script mostra o status atual de cada módulo antes de modificar.

Após aplicar, o bin patchado é salvo em `output/`.

### 5. Deploy no dispositivo

**Opção A — Via ADB (automático):**

Com o dispositivo conectado via USB e depuração ADB ativa:
1. Coloque o `PATCH_CAM.zip` (módulo Magisk base) em `output/`
2. No menu, escolha `[I]` — o script injeta o bin no zip e instala via Magisk, reiniciando o dispositivo automaticamente

**Opção B — Manual:**

1. Escolha `[Z]` para gerar o `PATCH_CAM.zip` atualizado
2. Transfira o zip para o dispositivo
3. Instale pelo Magisk Manager como módulo normal

---

## Etapas de patch

| Etapa | Módulo(s) | Efeito ao desabilitar | Risco |
|---|---|---|---|
| 1 — ANR | `anr10_ipe` | Devolve textura e grão natural. Elimina suavização excessiva. | 🟢 Baixo |
| 2 — HNR + LENR | `hnr10_ipe`, `lenr10_ipe` | Remove NR híbrido e de baixa exposição. Complementa Etapa 1. | 🟢 Baixo |
| 3 — ASF | `asf30_ipe` | Desliga sharpening adaptativo. Imagem mais orgânica. | 🟢 Baixo |
| 4 — GTM | `gtm10_ife`, `gtm13_ipe` | Curva de tom mais linear. Reduz queima de altas luzes. | 🟡 Médio |
| 5 — LTM | `ltm13~16_ipe` | Reduz HDR artificial e sombras comprimidas por região. | 🟡 Médio |
| 6 — TMC | `tmc10~13_sw` | Desliga controle global de tone mapping. | 🟡 Médio |
| 7 — GAMMA | `gamma16_ife/ipe` | ⚠️ Pode gerar imagem preta. **Apenas para teste experimental.** | 🔴 Alto |
| 8 — MF | `mf10_sw`, `mf11_sw` | Desliga multi-frame. Elimina ghosting em cenas com movimento. | 🟡 Médio |
| 9 — TF/MFNR | `tf10_ipe`, `tf20_ipe` | Principal causa do efeito sabonete. **Requer Etapa 1 aplicada antes.** | 🟡 Médio |

### Recomendação de início

Para corrigir o efeito sabonete com menor risco:

```
Etapa 1 (ANR ALL) → Etapa 9 (TF v10 + v20)
```

Para uma limpeza completa, use `[A]` — aplica todas as etapas exceto Gamma.

---

## Indicadores de status

O script exibe o estado atual de cada módulo no binário:

| Ícone | Significado |
|---|---|
| 🟢 DEFAULT | Valor original da Xiaomi (módulo ativo) |
| 🔴 PATCHADO | Módulo desabilitado pelo patcher |
| 🟡 PARCIAL | Alguns perfis modificados, outros não |
| ⚪ não encontrado | Módulo não presente neste binário |

---

## Avisos importantes

- **Sempre mantenha backup do `.bin` original** antes de qualquer patch. O script nunca sobrescreve o arquivo em `input/`, apenas grava em `output/`.
- O patch na **Etapa 9 (TF/MFNR)** requer que a **Etapa 1 (ANR)** esteja aplicada — o script avisa e oferece incluir automaticamente caso você esqueça.
- A **Etapa 7 (Gamma)** pode resultar em imagem completamente preta ou corrompida. Use apenas para fins de teste/diagnóstico, nunca em produção.
- Este patcher modifica o binário Chromatix localmente no PC. **Nenhum comando root é executado no PC** — root só é necessário no dispositivo para que o módulo Magisk funcione.

---

## Compatibilidade de ROMs

Testado com:
- `xiaomi.eu` V14 Android 13 (Snapdragon 888)
- MIUI Global / China baseadas em Android 12/13 para `vili`

O nome do binário pode variar conforme a ROM. Use `[L]` no menu para carregar um arquivo com nome diferente.

---

## Licença

MIT License — use, modifique e distribua livremente.
