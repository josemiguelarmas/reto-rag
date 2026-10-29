# Demo Taller 2 · Memoria, contexto y MCP


## Sesión 1

Herramientas disponibles: `buscar_procesos, consultar_empresa, calcular_indicadores, buscar_en_pliegos, listar_documentos`


**Usuario:** Hola, soy Laura, la gerente de licitaciones de la empresa. Nos interesan sobre todo obras de mantenimiento de edificaciones en Santander.

**Analista:** Excelente. En Santander hay **2 procesos disponibles**, y uno es exactamente lo que buscan:

**FLO-INFRA-SA-MC-007-2025** — *Adecuación y mantenimiento de algunas instalaciones del Palacio Municipal* (Floridablanca, Santander)
- **Tipo:** Obra
- **Modalidad:** Selección Abreviada de Menor Cuantía
- **Presupuesto:** $305.813.941
- **Duración:** 2 meses
- **Publicación:** 30 de diciembre de 2025
- **Estado:** Adjudicado a CONSTRUOBRAS ISAVAL S.A.S por $305.644.297
- **Respuestas:** 3 ofertas recibidas

**Nota importante:** Este proceso ya fue adjudicado hace pocos días, así que la oportunidad cerró.

El otro proceso (SINF-CPS-050-23) es de prestación de servicios profesionales para un ingeniero civil, no es obra.

¿Quiere que revisemos los requisitos y la estructura de este proceso de la Alcaldía para futuras oportunidades similares, o prefiere que busquemos en otras regiones o con otros criterios?

Fuentes: SECOP II, datos abiertos (referencia FLO-INFRA-SA-MC-007-2025 y SINF-CPS-050-23).

_herramientas: buscar_procesos, buscar_procesos, buscar_procesos · 14834+744 tokens · 8.41 s_


**Usuario:** ¿Qué índice de liquidez y qué experiencia exige el proceso de la Alcaldía de Floridablanca?

**Analista:** **Índice de liquidez:** ≥ 1.8

**Experiencia:** Máximo 4 contratos inscritos en el RUP con códigos UNSPSC 72101500 o 72152700, cuya suma sea ≥ 100 % del presupuesto oficial (en SMMLV). Al menos uno debe valer ≥ 50 % del presupuesto oficial.

En pesos, el presupuesto es $305.813.941. Convertido a SMMLV (con el salario mínimo vigente de 2025, ~$320.000), equivale aproximadamente a **956 SMMLV**, así que la experiencia requerida debe sumar 956 SMMLV mínimo.

¿Quiere que verifiquemos si nuestra empresa cumple estos requisitos?

Fuentes: 14_FLO_INFRA_SA_MC_007_2025.pdf, p. 2, secciones «5. Capacidad financiera y organizacional» y «6. Experiencia del proponente».

_herramientas: buscar_en_pliegos, buscar_en_pliegos · 9686+488 tokens · 9.08 s_


**Usuario:** ¿Cumplimos los requisitos financieros de ese proceso? ¿Nos conviene presentarnos?

**Analista:** **No cumple el requisito financiero clave:**

| Indicador | Exigido | Nuestra empresa | ¿Cumple? |
|-----------|---------|-----------------|----------|
| **Índice de liquidez** | ≥ 1.8 | 1.7 | ❌ No |

Nuestro índice de liquidez es **1.7**, pero el proceso exige **1.8 mínimo**. La diferencia es pequeña (0.1 puntos), pero es insuficiente.

**Situación financiera general:**
- Endeudamiento: 62% ✓
- Razón de cobertura de intereses: 2.5 ✓
- Capital de trabajo: $182 millones (cubre el 59.5% del presupuesto)

**Experiencia:** Sí cumplimos. Tenemos 4 contratos con códigos UNSPSC 72101500 y 72152700 (la empresa tiene ambos en su RUP vigente), y el contrato EXP-3 con el Municipio de Palmira ($280 millones en 2024) cubre más del 50% del presupuesto requerido ($306 millones).

**Recomendación:** **No presentarse en este proceso.** El fallo en liquidez lo descalificaría en el acto. Sugiero que antes de participar en futuros procesos de esta magnitud, refuercen el capital de trabajo para mejorar este indicador.

Fuentes: Cálculo con los estados financieros de la empresa (corte 2025-12-31); Perfil de la empresa (empresa.json); 14_FLO_INFRA_SA_MC_007_2025.pdf, p. 2, sección «5. Capacidad financiera y organizacional».

_herramientas: consultar_empresa, calcular_indicadores · 8704+567 tokens · 7.04 s_


**Usuario:** ¿Qué garantía de seriedad de la oferta exige el estudio previo del DANE EDP-545-2022?

**Analista:** **No lo sé:** el documento no exige garantía de seriedad de la oferta. Solo exige **garantía de cumplimiento del 10 % del valor del contrato** ($57.333.333), con vigencia igual al plazo más 4 meses adicionales.

En este proceso de contratación directa (servicios profesionales para el DANE), no hay fase de ofertas competitivas, así que no aplica garantía de seriedad.

Fuentes: 01_EDP_545_2022.pdf, p. 2, sección «7. Garantías».

_herramientas: listar_documentos, buscar_en_pliegos · 17117+389 tokens · 5.57 s_


**Usuario:** ¿Quién ganó el mundial de fútbol de 2022?

**Analista:** No lo sé: esa pregunta es ajena a la contratación pública colombiana y los procesos del SECOP II. No puedo ayudarle con ese tema.

¿Hay algo más sobre los procesos disponibles o los requisitos de nuestra empresa que quiera revisar?

_herramientas: ninguna · 4643+72 tokens · 1.25 s_


> Memoria a largo plazo tras la sesión: ['Laura es gerente de licitaciones de la empresa', 'La empresa se interesa principalmente en procesos de obras de mantenimiento de edificaciones en Santander', 'La empresa tiene un índice de liquidez de 1.7, por debajo del mínimo exigido en procesos de obra significativos (1.8)', 'La empresa posee experiencia comprobada en códigos UNSPSC 72101500 y 72152700 con 4 contratos inscritos en el RUP']
>
> Resumen guardado (medio plazo): ['**Resumen actualizado:**\n\n**Contacto:** Laura, gerente de licitaciones de la empresa.\n\n**Interés:** Obras de mantenimiento de edificaciones en Santander.\n\n**Proceso consultado:**\n- FLO-INFRA-SA-MC-007-2025 (Alcaldía de Floridablanca): Adecuación y mantenimiento Palacio Municipal. Presupuesto $305.813.941. Estado: Adjudicado. Requisitos financieros: liquidez ≥1.8, endeudamiento ≤65%. Experiencia: máximo 4 contratos UNSPSC 72101500 o 72152700, suma ≥100% del presupuesto, al menos uno ≥50%.\n\n**Conclusión:** La empresa no cumple liquidez (tiene 1.7, exige 1.8). Cumple experiencia.\n\n**Decisión:** No presentarse al proceso FLO-INFRA-SA-MC-007-2025.\n\n**Recomendación:** Reforzar capital de trabajo antes de participar en procesos de esta magnitud.\n\n**Proceso adicional revisado:**\n- EDP-545-2022 (DANE): Servicios profesionales. Garantía de cumplimiento: 10% del valor del contrato.']


## Sesión 2


**Usuario:** ¿Recuerdas quién soy y qué proceso revisamos la vez pasada?

**Analista:** Claro, Laura. Usted es gerente de licitaciones de su empresa, que se interesa en procesos de obras de mantenimiento de edificaciones en Santander.

La vez pasada revisamos el proceso **FLO-INFRA-SA-MC-007-2025** de la Alcaldía de Floridablanca (Adecuación y mantenimiento Palacio Municipal, presupuesto $305.813.941). Determinamos que su empresa **no cumple el requisito de liquidez** (tiene 1.7, pero se exige 1.8), aunque sí cumple la experiencia requerida. La recomendación fue no presentarse y reforzar el capital de trabajo antes de participar en procesos de esa magnitud.

¿Hay algo nuevo que quiera revisar, o desea explorar otros procesos similares en Santander?

Fuentes: Memoria de sesiones anteriores.

_herramientas: ninguna · 3675+225 tokens · 2.76 s_


**Usuario:** ¿Cuántas ofertas recibió el proceso LP-DT-CAU-003-2019 y qué experiencia exige su pliego?

**Analista:** El proceso **LP-DT-CAU-003-2019** (INVIAS, mantenimiento rutinario de vías Cauca) recibió **51 ofertas** (SECOP II, datos abiertos).

En cuanto a experiencia, el pliego exige: **máximo 3 contratos inscritos en el RUP, clasificados en al menos uno de los códigos UNSPSC 72141000, con sumatoria igual o superior al 100 % del presupuesto oficial expresado en SMMLV. Al menos uno de los contratos deberá tener un valor igual o superior al 50 % del presupuesto oficial** (Pliego de condiciones definitivo, p. 2, sección 7).

Fuentes: SECOP II, datos abiertos (LP-DT-CAU-003-2019); 13_LP_DT_CAU_003_2019.pdf, p. 2, sección «7. Experiencia del proponente».

_herramientas: buscar_procesos, buscar_en_pliegos · 9812+415 tokens · 7.09 s_


> Memoria a largo plazo tras la sesión: ['Laura es gerente de licitaciones de la empresa', 'La empresa se interesa principalmente en procesos de obras de mantenimiento de edificaciones en Santander', 'La empresa tiene un índice de liquidez de 1.7, por debajo del mínimo exigido en procesos de obra significativos (1.8)', 'La empresa posee experiencia comprobada en códigos UNSPSC 72101500 y 72152700 con 4 contratos inscritos en el RUP']
>
> Resumen guardado (medio plazo): ['**Resumen actualizado:**\n\n**Usuario:** Laura, gerente de licitaciones.\n\n**Procesos consultados:**\n- **FLO-INFRA-SA-MC-007-2025** (Alcaldía Floridablanca, mantenimiento Palacio Municipal, $305.813.941): No cumple liquidez (1.7 vs. 1.8 requerido). Sí cumple experiencia.\n- **LP-DT-CAU-003-2019** (INVIAS, mantenimiento vías Cauca): 51 ofertas recibidas. Exige máximo 3 contratos RUP en UNSPSC 72141000, sumatoria ≥100% presupuesto oficial en SMMLV; mínimo uno ≥50% presupuesto oficial.\n\n**Conclusión:** Empresa necesita reforzar capital de trabajo antes de participar en procesos de magnitud similar.\n\n**Preferencias:** Procesos de obras mantenimiento edificaciones en Santander.']
