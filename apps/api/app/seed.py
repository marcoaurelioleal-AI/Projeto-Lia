from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .config import settings
from .models import (
    ChecklistRun,
    ChecklistRunItem,
    ChecklistTemplate,
    ChecklistTemplateItem,
    Manual,
    ManualSection,
    ManualStep,
    Store,
    User,
)
from .security import hash_password


MANUALS_SEED = [
    {
        "unit": "Lia Burguer",
        "title": "Procedimento de Chapa e Montagem",
        "temperature": "200°C constante",
        "time_standard": "2:30 min por lado para ponto médio",
        "critical_point": "Não prensar a carne",
        "tip": "Nunca pressione a carne com a espátula; isso tira suco, sabor e padrão do lanche.",
        "sections": {
            "Preparo da chapa": [
                "Pré-aquecer a chapa antes do primeiro pedido.",
                "Manter a área seca, limpa e sem excesso de gordura queimada.",
                "Separar pão, queijo, molhos e embalagem antes de iniciar a carne.",
            ],
            "Carne e montagem": [
                "Selar a carne sem pressionar para preservar suculência.",
                "Adicionar queijo no tempo correto para derreter sem ressecar.",
                "Montar o lanche seguindo a ordem padrão da casa.",
                "Conferir adicionais antes de fechar a embalagem.",
            ],
            "Controle de qualidade": [
                "Verificar ponto, temperatura e apresentação antes de liberar.",
                "Trocar utensílios quando houver contaminação cruzada.",
                "Descartar insumos fora do padrão de aparência ou validade.",
            ],
        },
    },
    {
        "unit": "Lia Pizza",
        "title": "Procedimento de Forno, Montagem e Finalização",
        "temperature": "280°C a 320°C, conforme forno",
        "time_standard": "6 a 9 min, ajustando por massa e recheio",
        "critical_point": "Assar base e cobertura por igual",
        "tip": "Pizza bonita começa no porcionamento. Excesso de recheio atrasa forno e derruba margem.",
        "sections": {
            "Preparação": [
                "Conferir massa, molho, queijo e recheios antes de abrir pedido.",
                "Usar porcionamento padrão para evitar desperdício e variação de custo.",
                "Espalhar molho sem encharcar a massa.",
            ],
            "Forno": [
                "Pré-aquecer o forno e evitar abrir a porta sem necessidade.",
                "Girar a pizza quando houver diferença de calor entre os lados.",
                "Retirar quando borda, base e queijo estiverem no padrão.",
            ],
            "Corte e entrega": [
                "Cortar com rolete limpo e adequado.",
                "Conferir sabor, tamanho, borda e observações do pedido.",
                "Embalar de forma firme para não deslocar cobertura no delivery.",
            ],
        },
    },
    {
        "unit": "Lia Salgados",
        "title": "Procedimento de Fritura, Estufa e Validade",
        "temperature": "170°C a 180°C no óleo",
        "time_standard": "3 a 5 min, conforme tamanho e recheio",
        "critical_point": "Óleo limpo e temperatura estável",
        "tip": "Temperatura baixa encharca; temperatura alta doura por fora e deixa frio por dentro.",
        "sections": {
            "Fritura": [
                "Aquecer o óleo antes de colocar os salgados.",
                "Não sobrecarregar o cesto para evitar queda brusca de temperatura.",
                "Escorrer bem antes de levar para a estufa ou embalagem.",
            ],
            "Estufa e exposição": [
                "Manter salgados organizados por tipo e lote.",
                "Controlar tempo de exposição para preservar textura e segurança.",
                "Retirar itens ressecados, rachados ou fora do padrão visual.",
            ],
            "Controle de validade": [
                "Identificar lotes e respeitar ordem de produção.",
                "Verificar validade de recheios, massas e bebidas diariamente.",
                "Registrar perdas para melhorar compra e produção.",
            ],
        },
    },
]


CHECKLISTS_SEED = [
    {
        "title": "Limpeza da Loja",
        "category": "limpeza",
        "items": {
            "Segunda-feira": [
                "Limpar geladeiras de refrigerante.",
                "Retirar itens do armário preto e limpar prateleiras.",
                "Organizar bebidas e verificar validade.",
                "Revisar estoque aberto e itens próximos do vencimento.",
            ],
            "Diariamente": [
                "Lavar a frente da loja.",
                "Manter balcões limpos no início, durante e fim do expediente.",
                "Limpar paredes quando necessário.",
                "Organizar e limpar a parte debaixo do balcão.",
                "Higienizar áreas de manipulação e utensílios críticos.",
            ],
            "Sexta-feira": [
                "Lavar as duas lojas.",
                "Lavar bandejas.",
                "Lavar porta molhos e porta guardanapos.",
                "Reforçar limpeza para o fim de semana.",
            ],
        },
    },
    {
        "title": "Atendimento Delivery",
        "category": "delivery",
        "items": {
            "Diariamente": [
                "Verificar mensagens pendentes.",
                "Verificar tempo de entrega.",
                "Conferir cardápio de pizza e salgado.",
                "Preparar relatórios e planilha de motoboys.",
                "Abrir os 3 caixas.",
                "Enviar avaliações do iFood e WhatsApp.",
                "Mandar Falaaê pendentes do dia anterior.",
                "Pedir dinheiro para pagamento de motoboys; na sexta, prever fim de semana.",
                "Fazer molho, mantendo mínimo de duas caixas na loja.",
                "Verificar se há máquinas para troca.",
                "Colocar máquinas para carregar.",
            ],
            "Fechamento": [
                "Iniciar fechamento dos caixas a partir de 22:30.",
                "Fazer pagamento dos motoboys.",
                "Enviar relatórios.",
                "Retirar o lixo.",
                "Desligar o ar-condicionado.",
                "Organizar a loja para o próximo dia.",
            ],
        },
    },
    {
        "title": "Produção e Estoque",
        "category": "estoque",
        "items": {
            "Antes do pico": [
                "Conferir insumos críticos de hambúrguer, pizza e salgados.",
                "Separar embalagens, sacolas, molhos e descartáveis.",
                "Confirmar funcionamento de chapa, forno, fritadeira e maquininhas.",
            ],
            "Controle de perdas": [
                "Registrar itens descartados por validade, erro ou quebra de padrão.",
                "Sinalizar produtos com giro baixo para ajuste de produção.",
                "Conferir validade de bebidas, molhos, massas e recheios.",
            ],
        },
    },
]


def seed_database(db: Session) -> None:
    seed_admin(db)
    seed_stores(db)
    seed_manuals(db)
    seed_checklist_templates(db)
    db.commit()


def seed_admin(db: Session) -> None:
    exists = db.scalar(select(User).where(User.username == settings.default_admin_username))
    if exists:
        return
    db.add(
        User(
            username=settings.default_admin_username,
            name="Administrador LIA",
            role="admin",
            password_hash=hash_password(settings.default_admin_password),
        )
    )


def seed_stores(db: Session) -> None:
    for name in ("Grupo Lia", "Lia Burguer", "Lia Pizza", "Lia Salgados"):
        if not db.scalar(select(Store.id).where(Store.name == name)):
            db.add(Store(name=name, active=True))


def seed_manuals(db: Session) -> None:
    if db.scalar(select(Manual.id).limit(1)):
        return
    for manual_data in MANUALS_SEED:
        manual = Manual(
            unit=manual_data["unit"],
            title=manual_data["title"],
            temperature=manual_data["temperature"],
            time_standard=manual_data["time_standard"],
            critical_point=manual_data["critical_point"],
            tip=manual_data["tip"],
        )
        for section_index, (section_title, steps) in enumerate(manual_data["sections"].items()):
            section = ManualSection(title=section_title, position=section_index)
            for step_index, step in enumerate(steps):
                section.steps.append(ManualStep(text=step, position=step_index))
            manual.sections.append(section)
        db.add(manual)


def seed_checklist_templates(db: Session) -> None:
    if db.scalar(select(ChecklistTemplate.id).limit(1)):
        return
    for template_data in CHECKLISTS_SEED:
        template = ChecklistTemplate(title=template_data["title"], category=template_data["category"])
        position = 0
        for section, items in template_data["items"].items():
            for item in items:
                template.items.append(ChecklistTemplateItem(section=section, text=item, position=position))
                position += 1
        db.add(template)


def ensure_runs_for_date(db: Session, run_date: date, store: str) -> list[ChecklistRun]:
    templates = db.scalars(
        select(ChecklistTemplate).options(selectinload(ChecklistTemplate.items)).order_by(ChecklistTemplate.id)
    ).all()
    runs: list[ChecklistRun] = []

    for template in templates:
        run = db.scalar(
            select(ChecklistRun)
            .options(selectinload(ChecklistRun.items).selectinload(ChecklistRunItem.template_item))
            .where(
                ChecklistRun.template_id == template.id,
                ChecklistRun.run_date == run_date,
                ChecklistRun.store == store,
            )
        )
        if not run:
            run = ChecklistRun(template_id=template.id, run_date=run_date, store=store)
            for item in template.items:
                run.items.append(ChecklistRunItem(template_item_id=item.id))
            db.add(run)
            db.flush()
        runs.append(run)

    db.commit()
    return db.scalars(
        select(ChecklistRun)
        .options(
            selectinload(ChecklistRun.template),
            selectinload(ChecklistRun.items).selectinload(ChecklistRunItem.template_item),
            selectinload(ChecklistRun.items).selectinload(ChecklistRunItem.completed_by),
        )
        .where(ChecklistRun.run_date == run_date, ChecklistRun.store == store)
        .order_by(ChecklistRun.id)
    ).all()
