import json
import subprocess

# -------------------------------------------------------------
# FS 4-400 EMBT
# -------------------------------------------------------------
data_400 = {
  "slug": "ventilador-exaustor-axial-400mm-fs-4-400-embt",
  "nome": "Ventilador Exaustor Axial 400mm FS 4-400 EMBT",
  "sku": "FS 4-400 EMBT",
  "categoria": "Ventiladores Axiais",
  "pdf_fonte": "FS4-400EMBT.pdf",
  "especificacoes": [
    {"atributo": "Diâmetro / Hélice", "valor": "400 mm", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Tensão Nominal", "valor": "220 V", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Alimentação", "valor": "Monofásica", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Corrente Nominal", "valor": "1,20/1,35 A", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Potência Consumida", "valor": "180/260 W", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Frequência", "valor": "50/60 Hz", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Rotação", "valor": "1390/1590 RPM", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Vazão Máxima", "valor": "Até ~4300 m³/h", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Grau de Proteção", "valor": "IP-54", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Nível de Ruído", "valor": "67/72 dBA", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Temperatura de Operação", "valor": "-40 °C (Com graxa anticongelante)", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Mancais", "valor": "Rolamento de esferas blindado (2Z)", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Capacitor", "valor": "6 µF", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Isolação", "valor": "Classe F", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Peso", "valor": "6,0 kg", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"}
  ],
  "seo": {
    "keywords": ["ventilador fs 4-400 embt", "exaustor 400mm baixa temperatura", "sell-parts fs 4-400 embt"],
    "meta_description": "Ventilador Exaustor Axial 400mm FS 4-400 EMBT 220 V. Preparado para -40ºC com graxa anticongelante, proteção mecânica IP-54, rotor externo. Ficha garantida."
  },
  "resumo_tecnico": "O Ventilador Exaustor Axial 400mm – FS 4-400 EMBT é um equipamento de alta robustez desenvolvido especificamente para sistemas de refrigeração que operam em baixas temperaturas (BT). Construído com motor de rotor externo e hélice em chapa de aço protegida por pintura a pó poliéster, o modelo suporta operações frigoríficas exigentes, mantendo a integridade estrutural em câmaras frias.\n\nEquipado com rolamentos blindados (2Z) e lubrificado com graxa anticongelante especial, este equipamento garante operação ininterrupta em até -40 °C. O conjunto possui caixa de ligação em polipropileno com prensa cabos e grau de proteção adequado, prevenindo o congelamento de contatos elétricos e facilitando a integração em evaporadores e unidades condensadoras.",
  "hero_checklist": [
    "Operação em Baixa Temperatura (-40ºC)",
    "Rolamento com Graxa Anticongelante",
    "Grau de Proteção IP-54"
  ],
  "beneficios": [
    {
      "titulo": "Adequação para Frio Extremo",
      "descricao": "Lubrificação especial dos rolamentos com graxa anticongelante permite o funcionamento mecânico contínuo em ambientes frigoríficos rigorosos de até -40 °C."
    },
    {
      "titulo": "Proteção Elétrica em Câmaras Frias",
      "descricao": "Caixa de ligação em polipropileno aditivado com borne e prensa cabos blinda as conexões contra umidade e gelo, oferecendo operação elétrica segura."
    },
    {
      "titulo": "Resistência Estrutural Aprimorada",
      "descricao": "Construção integral em aço com pintura a pó em poliéster, prevenindo oxidação e degradação em ambientes com alta condensação e umidade."
    },
    {
      "titulo": "Desempenho Estável 24/7",
      "descricao": "O motor de rotor externo associado ao regime S1 proporciona exaustão e troca térmica ininterrupta em evaporadores de grande porte sem falhas prematuras."
    }
  ],
  "diferenciais": [
    "Lubrificação de rolamentos de fábrica com graxa anticongelante certificada para -40 °C.",
    "Grades de proteção e hélice em aço resistente para suportar vibrações em unidades condensadoras pesadas.",
    "Proteção térmica bimetálica interna para desligamento seguro em caso de variações severas no sistema elétrico.",
    "Garantia de procedência e suporte técnico especializado de engenharia da Sell-Parts para dimensionamento frigorífico."
  ],
  "mercados": [
    "Refrigeração comercial e cadeia do frio",
    "Centrais de distribuição e logística refrigerada",
    "Indústria alimentícia, frigoríficos e laticínios",
    "Siderurgia, metalurgia e mineração"
  ],
  "mercado": "O Ventilador FS 4-400 EMBT atende prioritariamente o mercado de Refrigeração comercial e cadeia do frio, com alta demanda em centrais de distribuição, armazéns climatizados e túneis de congelamento rápido.\n\nÉ amplamente utilizado na Indústria alimentícia, frigoríficos e laticínios para processos contínuos de conservação e ultracongelamento, além de atender a Siderurgia, metalurgia e mineração em processos que demandam exaustão mecânica pesada.",
  "aplicacoes_categoria": {
    "titulo": "Aplicações do Ventilador Exaustor Axial 400 mm",
    "intro": "Solução térmica de alta vazão e rotor externo, desenvolvida especificamente para exaustão e troca térmica em sistemas de refrigeração e frio industrial sob trabalho ininterrupto.",
    "cards": [
      {
        "titulo": "Circulação e Troca Térmica em Baixa Temperatura",
        "descricao": "Circulação forçada de ar em câmaras frigoríficas operando em temperaturas negativas (até -40 °C), garantindo homogeneidade térmica e evitando congelamento de componentes."
      },
      {
        "titulo": "Exaustão e Condensação Comercial",
        "descricao": "Extração forçada de calor em racks de condensação, blocos aletados de condensadores a ar e unidades frigoríficas de supermercados e atacarejos."
      },
      {
        "titulo": "Ventilação Forçada em Processos Industriais",
        "descricao": "Movimentação forçada de ar em ambientes industriais com alta carga térmica, salas de compressores e sistemas de exaustão pesada."
      }
    ]
  },
  "aplicacoes_equipamento": {
    "titulo": "Onde usar o Ventilador Exaustor Axial FS 4-400 EMBT",
    "intro": "Projetado com padrão de fixação de 470 mm e diâmetro de hélice de 400 mm, este modelo é empregado diretamente na estrutura dos seguintes equipamentos:",
    "cards": [
      {
        "titulo": "Evaporadores de Teto e Câmaras Frigoríficas",
        "descricao": "Evaporadores comerciais de alto perfil, forçadores de ar para câmaras frias, túneis de congelamento e salas de climatização."
      },
      {
        "titulo": "Condensadores a Ar e Racks Frigoríficos",
        "descricao": "Unidades condensadoras remotas, condensadores aletados a ar, racks de compressores e centrais de refrigeração."
      },
      {
        "titulo": "Chillers e Trocadores de Calor Industriais",
        "descricao": "Dry coolers industriais, resfriadores de líquidos, trocadores de calor aletados e sistemas de arrefecimento de processos."
      }
    ]
  },
  "faq": [
    {
      "pergunta": "O que significa a sigla 'BT' no modelo FS 4-400 EMBT?",
      "resposta": "A sigla 'BT' indica 'Baixa Temperatura'. Este modelo vem de fábrica com rolamentos lubrificados com uma graxa anticongelante especial, garantindo que o eixo não trave em operações de até -40 °C, sendo a escolha correta para câmaras frias e congelamento."
    },
    {
      "pergunta": "Qual a diferença prática no uso da graxa anticongelante neste exaustor?",
      "resposta": "Em motores convencionais sem preparação BT, a lubrificação dos rolamentos endurece em temperaturas negativas, causando travamento mecânico e queima do estator. A graxa anticongelante permite o movimento livre em até -40 °C, eliminando este risco."
    },
    {
      "pergunta": "A proteção IP-54 permite jatos diretos de água durante a lavagem da câmara?",
      "resposta": "A proteção mecânica IP-54 isola o motor contra poeira e respingos de água, comum na condensação. Porém, não suporta jatos de alta pressão diretos, que são comuns na higienização industrial. O equipamento deve ser protegido durante a lavagem do evaporador."
    },
    {
      "pergunta": "Como o protetor térmico bimetálico atua neste ventilador?",
      "resposta": "Se o equipamento sofrer um bloqueio por acúmulo excessivo de gelo na hélice, a corrente aumentará e o motor aquecerá. O bimetálico interno cortará a energia preventivamente para evitar a queima. Após o degelo e a queda da temperatura, o motor restabelecerá a operação."
    }
  ]
}

# Meta description length adjustment
desc_400 = data_400["seo"]["meta_description"]
if len(desc_400) < 150:
    data_400["seo"]["meta_description"] = data_400["seo"]["meta_description"].replace("Ficha garantida.", "Ficha técnica oficial garantida pela engenharia Sell-Parts.")
if len(data_400["seo"]["meta_description"]) > 160:
    data_400["seo"]["meta_description"] = data_400["seo"]["meta_description"][:160]

with open(r"c:\Users\comercial\Desktop\PROJETOS\Projeto landing pages\gerador\dados\ventilador-exaustor-axial-400mm-fs-4-400-embt.json", "w", encoding="utf-8") as f:
    json.dump(data_400, f, ensure_ascii=False, indent=2)

print("FS 4-400 EMBT JSON gerado com sucesso!")


# -------------------------------------------------------------
# FS 2-300 EM
# -------------------------------------------------------------
data_300 = {
  "slug": "ventilador-exaustor-axial-300mm-fs-2-300-em",
  "nome": "Ventilador Exaustor Axial 300mm FS 2-300 EM",
  "sku": "FS 2-300 EM",
  "categoria": "Ventiladores Axiais",
  "pdf_fonte": "FS2-300EM.pdf",
  "especificacoes": [
    {"atributo": "Diâmetro / Hélice", "valor": "300 mm", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Tensão Nominal", "valor": "220 V", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Corrente Nominal", "valor": "0,90/1,20 A", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Potência Consumida", "valor": "200/270 W", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Frequência", "valor": "50/60 Hz", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Rotação", "valor": "2750/3140 RPM", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Grau de Proteção", "valor": "IP-54", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Nível de Ruído", "valor": "72/75 dBA", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Temperatura de Operação", "valor": "-30 °C a 60 °C", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Mancais", "valor": "Rolamento de esferas blindado (2z)", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Capacitor", "valor": "6 µF", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Isolação", "valor": "Classe F", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Peso", "valor": "4,0 kg", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"},
    {"atributo": "Regime de Trabalho", "valor": "S1 (Contínuo)", "confianca": "100%", "fonte": "Datasheet Oficial Sell-Parts"}
  ],
  "seo": {
    "keywords": ["ventilador fs 2-300 em", "exaustor axial 300mm", "sell-parts fs 2-300 em"],
    "meta_description": "Ventilador Exaustor Axial 300mm FS 2-300 EM 220 V. Motor de rotor externo, proteção mecânica IP-54, rolamentos blindados 2z e 3140 RPM. Ficha garantida."
  },
  "resumo_tecnico": "O Ventilador Exaustor Axial 300mm – FS 2-300 EM é um equipamento robusto desenvolvido para aplicações industriais e frigoríficas de alta exigência. Com motor de rotor externo acoplado a uma hélice em chapa de aço e grade em fio de aço com pintura a pó poliéster preta, oferece excelente durabilidade estrutural contra impactos mecânicos, ideal para ambientes de montagem pesada.\n\nProjetado para regime S1 com mancais de rolamento blindados, o equipamento garante eficiência contínua na remoção de calor e troca térmica. Possui caixa de ligação em polipropileno com prensa cabos, simplificando a instalação em evaporadores, condensadores e sistemas de ventilação de estufas ou galpões industriais.",
  "hero_checklist": [
    "Motor de Rotor Externo",
    "Grau de Proteção IP-54",
    "Operação Ininterrupta 24/7"
  ],
  "beneficios": [
    {
      "titulo": "Resistência Estrutural Aprimorada",
      "descricao": "Grade e hélice fabricadas em aço com pintura a pó em poliéster, garantindo proteção contra desgastes operacionais severos em galpões e indústrias."
    },
    {
      "titulo": "Operação Ininterrupta e Segura",
      "descricao": "Mancais de rolamento de esferas blindados (2z) oferecem operação ininterrupta sem paradas forçadas de manutenção, suportando altas rotações de 3140 RPM."
    },
    {
      "titulo": "Instalação Elétrica Protegida",
      "descricao": "A caixa de ligação integrada conta com prensa cabos e borne de aterramento, protegendo as conexões contra intempéries e garantindo máxima segurança elétrica."
    },
    {
      "titulo": "Ampla Tolerância Térmica",
      "descricao": "Capacidade de operação estável em faixas extremas de temperatura (de frio intenso a alto calor), adaptando-se a variados processos térmicos industriais."
    }
  ],
  "diferenciais": [
    "Construção em aço com pintura a pó em poliéster resistente à corrosão severa.",
    "Mancais de esferas blindados (2z) para longo tempo de vida útil sem relubrificação.",
    "Proteção térmica bimetálica integrada para prevenção rigorosa de queimas por sobreaquecimento.",
    "Garantia de procedência e suporte técnico especializado de engenharia da Sell-Parts para pronta entrega."
  ],
  "mercados": [
    "Siderurgia, metalurgia e mineração",
    "Painéis elétricos, automação e data centers",
    "Refrigeração comercial e cadeia do frio",
    "Agronegócio e agroindústria",
    "Food service e equipamentos gastronômicos"
  ],
  "mercado": "O Ventilador FS 2-300 EM atende de forma massiva a Siderurgia, metalurgia e mineração em processos térmicos contínuos. Também é empregado fortemente no setor de Painéis elétricos, automação e data centers e Refrigeração comercial e cadeia do frio, além de Agronegócio e agroindústria e Food service e equipamentos gastronômicos.",
  "aplicacoes_categoria": {
    "titulo": "Aplicações do Ventilador Exaustor Axial 300 mm",
    "intro": "Solução térmica de alta rotação e rotor externo, projetada para exaustão e movimentação de ar em sistemas industriais e trocadores de calor sob trabalho contínuo.",
    "cards": [
      {
        "titulo": "Circulação e Troca Térmica Industrial",
        "descricao": "Exaustão localizada de ar quente, ventilação de fornos industriais, renovação de ar em cabines de operação e dissipação térmica em processos siderúrgicos."
      },
      {
        "titulo": "Arrefecimento de Condensadores e Evaporadores",
        "descricao": "Fluxo forçado de ar através de serpentinas aletadas para troca térmica em unidades frigoríficas comerciais e resfriamento de câmaras."
      },
      {
        "titulo": "Controle Térmico de Estruturas Elétricas",
        "descricao": "Extração de calor em salas de transformadores, bancos de capacitores, painéis elétricos de potência e nobreaks industriais."
      }
    ]
  },
  "aplicacoes_equipamento": {
    "titulo": "Onde usar o Ventilador Exaustor Axial FS 2-300 EM",
    "intro": "Projetado com padrão de fixação de 360 mm e diâmetro de hélice de 300 mm, este modelo é instalado diretamente na estrutura dos seguintes equipamentos:",
    "cards": [
      {
        "titulo": "Trocadores de Calor e Radiadores Industriais",
        "descricao": "Trocadores de calor a ar, radiadores de água e óleo industrial, chillers compactos e torres de arrefecimento."
      },
      {
        "titulo": "Condensadores a Ar e Unidades Frigoríficas",
        "descricao": "Unidades condensadoras comerciais, forçadores de ar compactos e balcões frigoríficos de média capacidade."
      },
      {
        "titulo": "Painéis Elétricos e Salas de Transformadores",
        "descricao": "Quadros de comando de alta potência, salas de transformadores elétricos, cubículos de média tensão e sistemas UPS."
      }
    ]
  },
  "faq": [
    {
      "pergunta": "Qual é a periodicidade recomendada para a manutenção dos mancais?",
      "resposta": "O equipamento utiliza rolamentos de esferas blindados (2z) lubrificados para toda a vida útil, dispensando relubrificação constante. A substituição só é necessária caso haja aumento anormal de ruído acústico ou vibração excessiva nas grades."
    },
    {
      "pergunta": "A proteção IP-54 permite instalação em áreas descobertas com chuva?",
      "resposta": "A proteção IP-54 protege contra acúmulo prejudicial de poeira e respingos de água de todas as direções, mas não foi projetada para submersão ou jatos fortes diretos constantes. Recomenda-se a instalação sob coberturas ou proteções mecânicas em áreas expostas."
    },
    {
      "pergunta": "Como deve ser feita a ligação do capacitor externo do equipamento?",
      "resposta": "O ventilador requer a utilização rigorosa de um capacitor de 6 µF, que deve ser conectado exatamente conforme o diagrama de ligação presente na caixa de bornes original. Um erro na ligação pode impedir o acionamento ou reduzir a vida útil elétrica do motor."
    },
    {
      "pergunta": "O equipamento aciona automaticamente caso sofra superaquecimento severo?",
      "resposta": "Sim, ele possui um protetor térmico bimetálico interno no estator do motor. Se a temperatura ultrapassar o limite seguro, ele interrompe a alimentação. Quando a temperatura da bobina cair, ele pode religar automaticamente; por isso, ao inspecionar, sempre desenergize totalmente o circuito."
    }
  ]
}

desc_300 = data_300["seo"]["meta_description"]
if len(desc_300) < 150:
    data_300["seo"]["meta_description"] = data_300["seo"]["meta_description"].replace("Ficha garantida.", "Ficha técnica oficial garantida pela engenharia Sell-Parts.")
if len(data_300["seo"]["meta_description"]) > 160:
    data_300["seo"]["meta_description"] = data_300["seo"]["meta_description"][:160]

with open(r"c:\Users\comercial\Desktop\PROJETOS\Projeto landing pages\gerador\dados\ventilador-exaustor-axial-300mm-fs-2-300-em.json", "w", encoding="utf-8") as f:
    json.dump(data_300, f, ensure_ascii=False, indent=2)

print("FS 2-300 EM JSON gerado com sucesso!")
