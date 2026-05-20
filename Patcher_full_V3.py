#!/usr/bin/env python3
"""
S5KHM2 Wide ISP Patcher — Xiaomi 11T Pro (vili / Snapdragon 888)
Patching por etapas para corrigir: efeito sabonete, altas luzes queimadas,
sombras esmagadas.

v2.3 — Menu principal: Magisk sempre visível + trocar lib sem fechar

Uso:
    python s5khm2_patcher.py
"""

import os
import shutil
import struct
import zipfile
import subprocess

DATA_SECTION_ADDR_POS = 184  # posição fixa no header QTI Chromatix

# ---------------------------------------------------------------------------
# Configuração do módulo Magisk
# ---------------------------------------------------------------------------
MAGISK_ZIP      = os.path.join('output', 'PATCH_CAM.zip')
MAGISK_BIN_PATH = 'system/vendor/lib64/camera/'  # caminho dentro do zip
ADB_DEVICE_PATH = '/sdcard/PATCH_CAM.zip'

# ---------------------------------------------------------------------------
# Definição de todos os patches
# ---------------------------------------------------------------------------
ALL_PATCHES = [

    # ── ETAPA 1: Ruído de Luminância e Crominância (ANR) ──────────────────
    {
        'id':             1,
        'etapa':          1,
        'patch_name':     'ANR — Luma + Chroma (ALL)',
        'descricao':      'Desliga todo o ANR. Devolve textura e grão natural.',
        'module_name':    'anr10_ipe',
        'address_offset': 35,
        'data_offset':    [0, 76, 80],
        'search':         '01',
        'replace':        '00',
    },
    {
        'id':             2,
        'etapa':          1,
        'patch_name':     'ANR — Somente Luma Noise Reduction',
        'descricao':      'Remove apenas suavização de brilho. Mantém NR de cor.',
        'module_name':    'anr10_ipe',
        'address_offset': 35,
        'data_offset':    76,
        'search':         '01',
        'replace':        '00',
    },
    {
        'id':             3,
        'etapa':          1,
        'patch_name':     'ANR — Somente Chroma Noise Reduction',
        'descricao':      'Remove apenas suavização de cor. Cores ficam mais reais.',
        'module_name':    'anr10_ipe',
        'address_offset': 35,
        'data_offset':    80,
        'search':         '01',
        'replace':        '00',
    },

    # ── ETAPA 2: Ruído Híbrido e Low Exposure NR ──────────────────────────
    {
        'id':             4,
        'etapa':          2,
        'patch_name':     'HNR — Hybrid Noise Reduction',
        'descricao':      'Desliga o filtro híbrido de ruído. Redundante quando ANR já está ativo.',
        'module_name':    'hnr10_ipe',
        'address_offset': 35,
        'data_offset':    0,
        'search':         '01',
        'replace':        '00',
    },
    {
        'id':             5,
        'etapa':          2,
        'patch_name':     'LENR — Low Exposure Noise Reduction',
        'descricao':      'Desliga NR específico para baixa exposição/high ISO.',
        'module_name':    'lenr10_ipe',
        'address_offset': 34,
        'data_offset':    0,
        'search':         '01',
        'replace':        '00',
    },

    # ── ETAPA 3: Sharpening / Edge Detection (ASF) ────────────────────────
    {
        'id':             6,
        'etapa':          3,
        'patch_name':     'ASF — Edge Detection ALL (Sharpening completo)',
        'descricao':      'Desliga todo o sharpening adaptativo. Imagem mais suave e natural.',
        'module_name':    'asf30_ipe',
        'address_offset': 35,
        'data_offset':    0,
        'search':         '01',
        'replace':        '00',
    },
    {
        'id':             7,
        'etapa':          3,
        'patch_name':     'ASF — Edge Detection Layer 1',
        'descricao':      'Desliga apenas a primeira camada de detecção de bordas.',
        'module_name':    'asf30_ipe',
        'address_offset': 35,
        'data_offset':    108,
        'search':         '01',
        'replace':        '00',
    },
    {
        'id':             8,
        'etapa':          3,
        'patch_name':     'ASF — Edge Detection Layer 2',
        'descricao':      'Desliga apenas a segunda camada de detecção de bordas.',
        'module_name':    'asf30_ipe',
        'address_offset': 35,
        'data_offset':    112,
        'search':         '01',
        'replace':        '00',
    },
    {
        'id':             9,
        'etapa':          3,
        'patch_name':     'ASF — Edge Detection Radial',
        'descricao':      'Desliga detecção radial de bordas (sharpening de centro/borda).',
        'module_name':    'asf30_ipe',
        'address_offset': 35,
        'data_offset':    116,
        'search':         '01',
        'replace':        '00',
    },
    {
        'id':             10,
        'etapa':          3,
        'patch_name':     'ASF — Edge Detection Contrast',
        'descricao':      'Desliga sharpening baseado em contraste.',
        'module_name':    'asf30_ipe',
        'address_offset': 35,
        'data_offset':    120,
        'search':         '01',
        'replace':        '00',
    },

    # ── ETAPA 4: Tone Mapping — Global (GTM) ──────────────────────────────
    {
        'id':             11,
        'etapa':          4,
        'patch_name':     'GTM v10 — Global Tone Mapping RAW (IFE)',
        'descricao':      'Desliga curva de tom global no sinal RAW. Exposição mais linear.',
        'module_name':    'gtm10_ife',
        'address_offset': 35,
        'data_offset':    0,
        'search':         '01',
        'replace':        '00',
    },
    {
        'id':             12,
        'etapa':          4,
        'patch_name':     'GTM v13 — Global Tone Mapping YUV 4:2:0 (IPE)',
        'descricao':      'Desliga curva de tom global no sinal YUV. Afeta JPEG/preview.',
        'module_name':    'gtm13_ipe',
        'address_offset': 35,
        'data_offset':    0,
        'search':         '01',
        'replace':        '00',
    },

    # ── ETAPA 5: Tone Mapping — Local (LTM) ───────────────────────────────
    {
        'id':             13,
        'etapa':          5,
        'patch_name':     'LTM v13 — Local Tone Mapping',
        'descricao':      'Desliga compressão local de tons v13.',
        'module_name':    'ltm13_ipe',
        'address_offset': 35,
        'data_offset':    0,
        'search':         '01',
        'replace':        '00',
    },
    {
        'id':             14,
        'etapa':          5,
        'patch_name':     'LTM v14 — Local Tone Mapping',
        'descricao':      'Desliga compressão local de tons v14. Reduz HDR artificial.',
        'module_name':    'ltm14_ipe',
        'address_offset': 35,
        'data_offset':    0,
        'search':         '01',
        'replace':        '00',
    },
    {
        'id':             15,
        'etapa':          5,
        'patch_name':     'LTM v15 — Local Tone Mapping',
        'descricao':      'Desliga compressão local de tons v15.',
        'module_name':    'ltm15_ipe',
        'address_offset': 35,
        'data_offset':    0,
        'search':         '01',
        'replace':        '00',
    },
    {
        'id':             16,
        'etapa':          5,
        'patch_name':     'LTM v16 — Local Tone Mapping',
        'descricao':      'Desliga compressão local de tons v16.',
        'module_name':    'ltm16_ipe',
        'address_offset': 35,
        'data_offset':    0,
        'search':         '01',
        'replace':        '00',
    },

    # ── ETAPA 6: Tone Mapping Control (TMC) ───────────────────────────────
    {
        'id':             17,
        'etapa':          6,
        'patch_name':     'TMC v10 — Tone Mapping Control',
        'descricao':      'Desliga controle global de tone mapping v10.',
        'module_name':    'tmc10_sw',
        'address_offset': 36,
        'data_offset':    0,
        'search':         '01',
        'replace':        '00',
    },
    {
        'id':             18,
        'etapa':          6,
        'patch_name':     'TMC v11 — Tone Mapping Control',
        'descricao':      'Desliga controle global de tone mapping v11.',
        'module_name':    'tmc11_sw',
        'address_offset': 36,
        'data_offset':    0,
        'search':         '01',
        'replace':        '00',
    },
    {
        'id':             19,
        'etapa':          6,
        'patch_name':     'TMC v12 — Tone Mapping Control',
        'descricao':      'Desliga controle global de tone mapping v12.',
        'module_name':    'tmc12_sw',
        'address_offset': 36,
        'data_offset':    0,
        'search':         '01',
        'replace':        '00',
    },
    {
        'id':             20,
        'etapa':          6,
        'patch_name':     'TMC v13 — Tone Mapping Control',
        'descricao':      'Desliga controle global de tone mapping v13.',
        'module_name':    'tmc13_sw',
        'address_offset': 36,
        'data_offset':    0,
        'search':         '01',
        'replace':        '00',
    },

    # ── ETAPA 7: Gamma ⚠️ APENAS TESTE ────────────────────────────────────
    {
        'id':             21,
        'etapa':          7,
        'patch_name':     'GAMMA IFE — RAW Gamma curve 65 dots ⚠️ APENAS TESTE',
        'descricao':      'Desliga curva gamma RAW (video/preview). NÃO usar em produção.',
        'module_name':    'gamma16_ife',
        'address_offset': 33,
        'data_offset':    0,
        'search':         '01',
        'replace':        '00',
    },
    {
        'id':             22,
        'etapa':          7,
        'patch_name':     'GAMMA IPE — YUV Gamma curve 257 dots ⚠️ APENAS TESTE',
        'descricao':      'Desliga curva gamma YUV (JPEG/video). NÃO usar em produção.',
        'module_name':    'gamma16_ipe',
        'address_offset': 33,
        'data_offset':    0,
        'search':         '01',
        'replace':        '00',
    },

    # ── ETAPA 8: Multi-Frame (MF) ──────────────────────────────────────────
    {
        'id':             23,
        'etapa':          8,
        'patch_name':     'MF v10 — Multi Frame (ghosting)',
        'descricao':      'Desliga multi-frame v10. Causa ghosting em cenas com movimento.',
        'module_name':    'mf10_sw',
        'address_offset': 37,
        'data_offset':    0,
        'search':         '01',
        'replace':        '00',
    },
    {
        'id':             24,
        'etapa':          8,
        'patch_name':     'MF v11 — Multi Frame (sharpening)',
        'descricao':      'Desliga multi-frame v11. Usado para sharpening, sem ghosting.',
        'module_name':    'mf11_sw',
        'address_offset': 37,
        'data_offset':    0,
        'search':         '01',
        'replace':        '00',
    },

    # ── ETAPA 9: Temporal Filter / MFNR ── requer ANR desligado ───────────
    {
        'id':             25,
        'etapa':          9,
        'patch_name':     'TF v10 — Temporal Filter / MFNR (OBRIGATÓRIO: desligar ANR antes)',
        'descricao':      'Desliga filtro temporal v10. Principal causa do efeito sabonete. '
                          'REQUER Etapa 1 (ANR ALL) aplicada antes.',
        'module_name':    'tf10_ipe',
        'address_offset': 36,
        'data_offset':    0,
        'search':         '01',
        'replace':        '00',
    },
    {
        'id':             26,
        'etapa':          9,
        'patch_name':     'TF v20 — Temporal Filter / MFNR (OBRIGATÓRIO: desligar ANR antes)',
        'descricao':      'Desliga filtro temporal v20. Pode causar mais ruído em cenas escuras. '
                          'REQUER Etapa 1 (ANR ALL) aplicada antes.',
        'module_name':    'tf20_ipe',
        'address_offset': 36,
        'data_offset':    0,
        'search':         '01',
        'replace':        '00',
    },
]

ETAPAS_INFO = {
    1: ('🧼 ETAPA 1', 'ANR — Luma + Chroma Noise Reduction',
        'Menor risco. Devolve textura e grão. Comece aqui.'),
    2: ('🧽 ETAPA 2', 'HNR + LENR — Hybrid e Low Exposure NR',
        'Complementa Etapa 1. Remove camadas redundantes de NR.'),
    3: ('✂️  ETAPA 3', 'ASF — Edge Detection / Sharpening',
        'Desliga sharpening adaptativo. Imagem mais natural.'),
    4: ('🌗 ETAPA 4', 'GTM — Global Tone Mapping RAW + YUV',
        'Corrige exposição linear. Reduz queima de altas luzes.'),
    5: ('🌓 ETAPA 5', 'LTM v13~v16 — Local Tone Mapping',
        'Reduz HDR artificial e sombras esmagadas por região.'),
    6: ('🎛️  ETAPA 6', 'TMC v10~v13 — Tone Mapping Control',
        'Desliga controle global de tone mapping.'),
    7: ('⚠️  ETAPA 7', 'GAMMA IFE + IPE — ⚠️ APENAS PARA TESTE',
        'NÃO desabilitar em produção. Apenas para experimentação.'),
    8: ('🎞️  ETAPA 8', 'MF v10/v11 — Multi Frame',
        'Desliga processamento multi-frame. v10 causa ghosting.'),
    9: ('💣 ETAPA 9', 'TF v10/v20 — Temporal Filter / MFNR',
        'MAIS AGRESSIVO. Requer Etapa 1 obrigatoriamente.'),
}

# ---------------------------------------------------------------------------
# Funções de patching
# ---------------------------------------------------------------------------

def le_int32(data, pos):
    """Lê 4 bytes little-endian como int."""
    return struct.unpack_from('<I', data, pos)[0]


def patch_modulo(data, datasection_offset, patch, interativo=False):
    """
    Aplica um patch em todas as ocorrências do módulo no binário.
    Suporta data_offset como int ou list de ints.
    Se interativo=True, pergunta um a um antes de aplicar.
    Retorna (data_modificada, n_modificados, n_ja_ok, n_total).
    """
    module_bytes  = patch['module_name'].encode()
    module_len    = len(module_bytes)
    search_bytes  = bytes.fromhex(patch['search'])
    replace_bytes = bytes.fromhex(patch['replace'])

    offsets = patch['data_offset']
    if not isinstance(offsets, list):
        offsets = [offsets]

    data = bytearray(data)
    
    instancias = []
    pos = 0
    while True:
        loc = data.find(module_bytes, pos)
        if loc == -1:
            break
        addr_pos     = loc + module_len + patch['address_offset']
        block_offset = le_int32(data, addr_pos)
        instancias.append((loc, block_offset))
        pos = loc + 1

    n_total = len(instancias)
    n_mod   = 0
    n_ja_ok = 0
    aplicar_todos = False

    for i, (loc, block_offset) in enumerate(instancias, start=1):
        inst_mod = 0
        inst_ja_ok = 0
        
        pode_modificar = False
        alvos = []
        for off in offsets:
            target = block_offset + datasection_offset + off
            alvos.append(target)
            if target < len(data):
                val = bytes([data[target]])
                if val == search_bytes:
                    pode_modificar = True
                elif val == replace_bytes:
                    inst_ja_ok += 1

        if inst_ja_ok == len(offsets):
            n_ja_ok += 1
            continue
            
        if pode_modificar:
            fazer_patch = True
            if interativo and not aplicar_todos:
                resp = input(f"    ▶ {patch['patch_name']} [{i}/{n_total}] -> ON. Aplicar patch? [s=sim / n=não / t=todos / q=sair]: ").strip().lower()
                if resp == 'q':
                    print("    Abortando os restantes...")
                    break
                elif resp == 't':
                    aplicar_todos = True
                elif resp == 's' or resp == '':
                    fazer_patch = True
                else:
                    fazer_patch = False
                    
            if fazer_patch:
                for target in alvos:
                    if target < len(data):
                        val = bytes([data[target]])
                        if val == search_bytes:
                            data[target:target + len(replace_bytes)] = replace_bytes
                            inst_mod += 1
                if inst_mod > 0:
                    n_mod += 1

    return bytes(data), n_mod, n_ja_ok, n_total


def get_patch_counts(data, datasection_offset, patch):
    """Retorna (on, off, outros, total) para um patch no binário."""
    module_bytes = patch['module_name'].encode()
    module_len   = len(module_bytes)
    total = on = off = outros = 0
    pos = 0

    offsets = patch['data_offset']
    if not isinstance(offsets, list):
        offsets = [offsets]

    while True:
        loc = data.find(module_bytes, pos)
        if loc == -1:
            break
        total += 1
        addr_pos     = loc + module_len + patch['address_offset']
        block_offset = le_int32(data, addr_pos)
        
        inst_on = 0
        inst_off = 0
        
        for off_val in offsets:
            target = block_offset + datasection_offset + off_val
            if target < len(data):
                v = data[target]
                if v == 0x01:
                    inst_on += 1
                elif v == 0x00:
                    inst_off += 1

        # Lógica: se tem algum ON, a chave mestre ou sub-chaves ainda não estão totalmente mortas.
        # Mas para patches múltiplos (ALL), se a principal (offset 0) for 0, as outras não importam.
        # Porém, pela UI, consideramos PATCHADO (OFF) se todas as verificadas estiverem OFF.
        # Se offset 0 (primeira do array) for 0, o módulo já está bypassado, então forçamos OFF
        # para alinhar com a expectativa visual de "desligado".
        
        primeiro_target = block_offset + datasection_offset + offsets[0]
        primeiro_desligado = False
        if primeiro_target < len(data) and data[primeiro_target] == 0x00:
            primeiro_desligado = True
            
        if inst_off == len(offsets) or primeiro_desligado:
            off += 1
        elif inst_on > 0:
            on += 1
        else:
            outros += 1

        pos = loc + 1
    return on, off, outros, total


def status_bin(data, datasection_offset, patches, titulo="STATUS DOS MÓDULOS"):
    """Mostra painel visual do estado atual de cada patch no arquivo."""
    print(f"\n{'─' * 90}")
    print(f"  📊 {titulo}")
    print(f"{'─' * 90}")

    etapa_atual = None
    for p in patches:
        # Cabeçalho de etapa
        if p['etapa'] != etapa_atual:
            etapa_atual = p['etapa']
            ei = ETAPAS_INFO[etapa_atual]
            print(f"\n  {ei[0]} — {ei[1]}")
            print(f"  {'ID':>3}  {'Módulo':<16} {'Patch':<42} {'Total':>6}  {'Status'}")
            print(f"  {'─'*3}  {'─'*16} {'─'*42} {'─'*6}  {'─'*25}")

        on, off, outros, total = get_patch_counts(data, datasection_offset, p)

        if total == 0:
            status = "⚪ não encontrado"
        elif on == total:
            status = "🟢 DEFAULT (tudo ON)"
        elif off == total:
            status = "🔴 PATCHADO (tudo OFF)"
        elif off > 0 and on > 0:
            status = f"🟡 PARCIAL ({on} ON / {off} OFF)"
        else:
            status = f"❓ outros ({outros})"

        nome_curto = p['patch_name'][:42]
        print(f"  {p['id']:>3}  {p['module_name']:<16} {nome_curto:<42} {total:>6}  {status}")

    print(f"\n{'─' * 90}")
    print(f"  🟢 DEFAULT = valor original da Xiaomi (ON)")
    print(f"  🔴 PATCHADO = módulo desabilitado (OFF)")
    print(f"  🟡 PARCIAL = alguns perfis modificados, outros não")
    print(f"{'─' * 90}\n")


# ---------------------------------------------------------------------------
# Auto-detecção do arquivo .bin na pasta input/
# ---------------------------------------------------------------------------

def detectar_bin():
    """Detecta automaticamente arquivos .bin na pasta input/."""
    os.makedirs('input', exist_ok=True)
    bins = [f for f in os.listdir('input') if f.endswith('.bin')]
    if not bins:
        return None
    if len(bins) == 1:
        return bins[0]
    # Múltiplos arquivos — deixa usuário escolher
    print("\n  Múltiplos arquivos .bin encontrados na pasta input/:")
    for i, b in enumerate(bins):
        print(f"  [{i}] {b}")
    while True:
        try:
            idx = int(input("\n  Escolha o número do arquivo: ").strip())
            if 0 <= idx < len(bins):
                return bins[idx]
        except ValueError:
            pass
        print("  Opção inválida.")


# ---------------------------------------------------------------------------
# Magisk ZIP — atualizar bin e instalar via ADB
# ---------------------------------------------------------------------------

def magisk_atualizar_zip(bin_path, filename):
    """
    Injeta o bin patchado dentro do PATCH_CAM.zip no caminho correto.
    Preserva todos os outros arquivos do zip intactos.
    """
    if not os.path.exists(MAGISK_ZIP):
        print(f"\n⚠️  Módulo Magisk não encontrado: {MAGISK_ZIP}")
        print("   Coloque o PATCH_CAM.zip na pasta output/ e tente novamente.")
        return False

    zip_inner_path = MAGISK_BIN_PATH + filename

    # Lê todos os arquivos existentes no zip
    arquivos_existentes = {}
    with zipfile.ZipFile(MAGISK_ZIP, 'r') as zf:
        for item in zf.infolist():
            arquivos_existentes[item.filename] = zf.read(item.filename)

    # Substitui ou adiciona o bin patchado
    with open(bin_path, 'rb') as f:
        arquivos_existentes[zip_inner_path] = f.read()

    # Reescreve o zip completo
    tmp_zip = MAGISK_ZIP + '.tmp'
    with zipfile.ZipFile(tmp_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for nome, dados in arquivos_existentes.items():
            zf.writestr(nome, dados)

    # No Windows, precisa remover o destino antes de renomear
    if os.path.exists(MAGISK_ZIP):
        os.remove(MAGISK_ZIP)
    os.rename(tmp_zip, MAGISK_ZIP)
    print(f"\n✅ Módulo Magisk atualizado: {MAGISK_ZIP}")
    print(f"   Bin injetado em: {zip_inner_path}")
    return True


def magisk_instalar_adb(filename):
    """
    Envia o PATCH_CAM.zip pro dispositivo via ADB e instala via Magisk.
    """
    print("\n📲 Instalando via ADB...")

    # Verifica se ADB está disponível
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=5)
        if 'device' not in result.stdout:
            print("❌ Nenhum dispositivo ADB conectado.")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("❌ ADB não encontrado. Verifique se está no PATH.")
        return False

    cmds = [
        (['adb', 'push', MAGISK_ZIP, ADB_DEVICE_PATH],
         f"Enviando {MAGISK_ZIP} → {ADB_DEVICE_PATH}"),
        (['adb', 'shell', f'su -c "magisk --install-module {ADB_DEVICE_PATH}"'],
         "Instalando módulo no Magisk"),
        (['adb', 'reboot'],
         "Reiniciando dispositivo"),
    ]

    for cmd, descricao in cmds:
        print(f"   ▶ {descricao}...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0 and 'reboot' not in cmd:
            print(f"   ❌ Erro: {result.stderr.strip() or result.stdout.strip()}")
            return False
        print(f"   ✅ OK")

    print("\n🔄 Dispositivo reiniciando... aguarde e teste a câmera!")
    return True


def menu_magisk(output_path, filename):
    """Menu pós-patch para atualizar zip e/ou instalar via ADB."""
    print("\n" + "─" * 70)
    print("  📦 MÓDULO MAGISK")
    print("─" * 70)
    print("  [Z] Atualizar PATCH_CAM.zip com o bin patchado")
    print("  [I] Atualizar zip E instalar via ADB (reinicia o aparelho)")
    print("  [P] Pular — só salvei o bin por enquanto")
    print("─" * 70)
    op = input("  Opção: ").strip().upper()

    if op == 'Z':
        magisk_atualizar_zip(output_path, filename)
    elif op == 'I':
        if magisk_atualizar_zip(output_path, filename):
            magisk_instalar_adb(filename)
    elif op == 'P':
        print("  Bin salvo em output/. Instale manualmente quando quiser.")


# ---------------------------------------------------------------------------
# Interface principal
# ---------------------------------------------------------------------------

def carregar_bin(filename=None):
    """
    Detecta ou solicita o arquivo .bin, carrega e retorna
    (filename, input_path, output_path, original_data, datasection_offset).
    Retorna None em caso de erro.
    """
    if filename is None:
        filename = detectar_bin()
        if filename:
            print(f"\n  🔍 Arquivo detectado automaticamente: {filename}")
            resp = input("  Usar este arquivo? (s/n): ").strip().lower()
            if resp != 's':
                filename = None

    if not filename:
        filename = input(
            '\nNome completo do arquivo .bin na pasta input/\n'
            'Exemplo: com_qti_tuned_vili_sunny_s5khm2_wide.bin\n'
            '> '
        ).strip()

    input_path  = os.path.join('input',  filename)
    output_path = os.path.join('output', filename)

    if not os.path.exists(input_path):
        print(f"\n❌ Arquivo não encontrado: {input_path}")
        return None

    with open(input_path, 'rb') as f:
        original_data = f.read()

    datasection_offset = le_int32(original_data, DATA_SECTION_ADDR_POS)
    print(f"\n  ✅ Arquivo carregado: {filename}")
    print(f"     {len(original_data):,} bytes  |  Data section offset: 0x{datasection_offset:X} ({datasection_offset})")
    return filename, input_path, output_path, original_data, datasection_offset


def main():
    print("=" * 70)
    print("  S5KHM2 Wide ISP Patcher v2.3 — Xiaomi 11T Pro (vili / SD888)")
    print("=" * 70)

    resultado = carregar_bin()
    if resultado is None:
        input("\nPressione Enter para fechar...")
        return
    filename, input_path, output_path, original_data, datasection_offset = resultado

    # Mostra status automaticamente na abertura
    fonte = "OUTPUT (já modificado)" if os.path.exists(output_path) else "INPUT (original / default Xiaomi)"
    with open(output_path if os.path.exists(output_path) else input_path, 'rb') as f:
        status_data = f.read()
    status_bin(status_data, datasection_offset, ALL_PATCHES, f"STATUS ATUAL — {fonte}")

    while True:
        zip_existe = os.path.exists(MAGISK_ZIP)
        output_existe = os.path.exists(output_path)

        print("─" * 70)
        print(f"  MENU PRINCIPAL  [{filename}]")
        print("─" * 70)
        print("  [S] Atualizar status dos módulos")
        print("  [L] Trocar arquivo .bin (carregar outra lib)")
        print("  [1] Etapa 1  — ANR Luma + Chroma (começa aqui)")
        print("  [2] Etapa 2  — HNR + LENR (Hybrid + Low Exposure NR)")
        print("  [3] Etapa 3  — ASF Sharpening / Edge Detection")
        print("  [4] Etapa 4  — GTM Global Tone Mapping RAW + YUV")
        print("  [5] Etapa 5  — LTM v13~v16 Local Tone Mapping")
        print("  [6] Etapa 6  — TMC v10~v13 Tone Mapping Control")
        print("  [7] Etapa 7  — GAMMA ⚠️  (APENAS TESTE, NÃO usar em prod)")
        print("  [8] Etapa 8  — MF v10/v11 Multi Frame")
        print("  [9] Etapa 9  — TF v10/v20 Temporal Filter / MFNR (agressivo)")
        print("  [A] Aplicar TODAS as etapas (exceto Gamma)")
        print("─" * 70)
        # Magisk — sempre visível, mas informa quando zip/output não existem
        zip_aviso = "" if zip_existe else "  ⚠️  (PATCH_CAM.zip não encontrado em output/)"
        out_aviso = "" if output_existe else "  ⚠️  (nenhum output gerado ainda)"
        print(f"  [Z] Atualizar PATCH_CAM.zip com o bin patchado{zip_aviso}{out_aviso}")
        print(f"  [I] Atualizar zip E instalar via ADB (reinicia o aparelho){zip_aviso}{out_aviso}")
        print("─" * 70)
        print("  [X] Sair")
        print("─" * 70)
        op = input("  Opção: ").strip().upper()

        if op == 'X':
            print("\nSaindo...\n")
            break

        elif op == 'S':
            if os.path.exists(output_path):
                with open(output_path, 'rb') as f:
                    cur_data = f.read()
                fonte = "OUTPUT (já modificado)"
            else:
                cur_data = original_data
                fonte = "INPUT (original / default Xiaomi)"
            status_bin(cur_data, datasection_offset, ALL_PATCHES, f"STATUS ATUAL — {fonte}")

        elif op == 'L':
            print("\n  Trocar arquivo .bin — deixe em branco para auto-detectar")
            novo = input("  Nome do arquivo (ou Enter para detectar): ").strip() or None
            resultado = carregar_bin(novo)
            if resultado is None:
                print("  ❌ Arquivo não carregado. Continuando com o anterior.")
                continue
            filename, input_path, output_path, original_data, datasection_offset = resultado
            fonte = "OUTPUT (já modificado)" if os.path.exists(output_path) else "INPUT (original / default Xiaomi)"
            with open(output_path if os.path.exists(output_path) else input_path, 'rb') as f:
                status_data = f.read()
            status_bin(status_data, datasection_offset, ALL_PATCHES, f"STATUS ATUAL — {fonte}")

        elif op in ('Z', 'I'):
            if not output_existe:
                print("\n  ❌ Nenhum output gerado ainda. Aplique ao menos um patch primeiro.")
                continue
            if op == 'Z':
                magisk_atualizar_zip(output_path, filename)
            else:
                if magisk_atualizar_zip(output_path, filename):
                    magisk_instalar_adb(filename)

        elif op in ('1','2','3','4','5','6','7','8','9','A'):
            if op == 'A':
                # Todas exceto Gamma (etapa 7) — sem submenu, aplica tudo direto
                etapas_sel = [1, 2, 3, 4, 5, 6, 8, 9]
                patches_candidatos = [p for p in ALL_PATCHES if p['etapa'] in etapas_sel]
            else:
                etapa_num = int(op)
                etapas_sel = [etapa_num]
                patches_candidatos = [p for p in ALL_PATCHES if p['etapa'] == etapa_num]

            # ── Submenu de seleção individual (só para etapas únicas) ─────────
            if op != 'A' and len(patches_candidatos) > 1:
                ei = ETAPAS_INFO[etapa_num]
                print(f"\n{'─' * 70}")
                print(f"  {ei[0]} — {ei[1]}")
                print(f"  {ei[2]}")
                print(f"{'─' * 70}")

                # Lê dados atuais para mostrar status inline
                cur_bin = output_path if os.path.exists(output_path) else input_path
                with open(cur_bin, 'rb') as f:
                    cur_data_sub = f.read()

                for i, p in enumerate(patches_candidatos, start=1):
                    on, off, outros, total = get_patch_counts(cur_data_sub, datasection_offset, p)
                    if total == 0:
                        st = "⚪ n/a"
                    elif off == total:
                        st = "🔴 OFF"
                    elif on == total:
                        st = "🟢 ON"
                    else:
                        st = f"🟡 {on}ON/{off}OFF"
                    print(f"  [{i}] {p['patch_name']}  ({st})")

                print(f"{'─' * 70}")
                print(f"  [T] Todos os patches acima")
                print(f"  [V] Voltar ao menu principal")
                print(f"{'─' * 70}")
                sel = input("  Escolha (números separados por vírgula, ex: 1,3): ").strip().upper()

                if sel == 'V':
                    continue
                elif sel == 'T':
                    patches_sel = patches_candidatos
                else:
                    indices_validos = set(range(1, len(patches_candidatos) + 1))
                    escolhidos = []
                    invalidos = []
                    for tok in sel.split(','):
                        tok = tok.strip()
                        try:
                            idx = int(tok)
                            if idx in indices_validos:
                                escolhidos.append(patches_candidatos[idx - 1])
                            else:
                                invalidos.append(tok)
                        except ValueError:
                            invalidos.append(tok)

                    if invalidos:
                        print(f"  ⚠️  Opções ignoradas (inválidas): {', '.join(invalidos)}")
                    if not escolhidos:
                        print("  Nenhum patch selecionado. Voltando.")
                        continue
                    patches_sel = escolhidos
            else:
                patches_sel = patches_candidatos

            # Aviso Gamma
            if any(p['etapa'] == 7 for p in patches_sel):
                print("\n⚠️  ATENÇÃO: O módulo GAMMA é apenas para teste!")
                print("   Desabilitá-lo pode causar imagem totalmente preta ou corrompida.")
                resp = input("   Confirma mesmo assim? (s/n): ").strip().lower()
                if resp != 's':
                    print("Cancelado.")
                    continue

            # Aviso TF sem ANR
            etapas_nos_patches = {p['etapa'] for p in patches_sel}
            if 9 in etapas_nos_patches and 1 not in etapas_nos_patches:
                print("\n⚠️  ATENÇÃO: A Etapa 9 (TF/MFNR) requer que o ANR esteja")
                print("   desligado (Etapa 1). Você deve aplicar a Etapa 1 também.")
                resp = input("   Incluir Etapa 1 automaticamente? (s/n): ").strip().lower()
                if resp == 's':
                    etapa1 = [p for p in ALL_PATCHES if p['etapa'] == 1]
                    patches_sel = etapa1 + patches_sel

            print(f"\n📋 Patches a aplicar ({len(patches_sel)}):")
            for p in patches_sel:
                ei = ETAPAS_INFO[p['etapa']]
                print(f"   [{ei[0]}] {p['patch_name']}")

            confirm = input("\nModo de aplicação: [T]odos de uma vez | [I]nterativo (um a um) | [C]ancelar: ").strip().upper()
            if confirm not in ('T', 'I'):
                print("Cancelado.")
                continue
            interativo = (confirm == 'I')

            if os.path.exists(output_path):
                with open(output_path, 'rb') as f:
                    work_data = f.read()
                print("   (continuando sobre o output existente)")
            else:
                work_data = original_data

            total_mod = 0
            print()
            for p in patches_sel:
                work_data, n_mod, n_ja_ok, n_total = patch_modulo(
                    work_data, datasection_offset, p, interativo=interativo
                )
                icone = '✅' if n_mod > 0 else ('⬛' if n_ja_ok == n_total else '⚠️')
                print(f"  {icone}  {p['patch_name']}")
                print(f"      {n_total} instâncias | {n_mod} modificadas | {n_ja_ok} já estavam OFF")
                total_mod += n_mod

            os.makedirs('output', exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(work_data)

            print(f"\n✅ Salvo em: {output_path}")
            print(f"   Total de bytes alterados: {total_mod} instâncias")

            # Mostra status atualizado automaticamente após aplicar
            status_bin(work_data, datasection_offset, ALL_PATCHES, "STATUS ATUALIZADO — OUTPUT")

            # Menu Magisk inline (mantido pós-patch para não quebrar fluxo habitual)
            menu_magisk(output_path, filename)

        else:
            print("Opção inválida.")

    input("\nPressione Enter para fechar...")


if __name__ == '__main__':
    main()