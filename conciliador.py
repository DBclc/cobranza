import pandas as pd
from io import BytesIO
from itertools import combinations

def buscar_combinaciones(df, columna, objetivo, tolerancia=1.0, max_comb=5):
    valores = df[columna].round(2).tolist()
    for r in range(1, min(max_comb, len(valores)) + 1):
        for combo in combinations(enumerate(valores), r):
            idxs, nums = zip(*combo)
            if abs(sum(nums) - objetivo) <= tolerancia:
                return df.iloc[list(idxs)]
    return pd.DataFrame()

def ejecutar_conciliacion_completa(excel_file):
    xls = pd.ExcelFile(excel_file)
    bancos = pd.read_excel(xls, "COMPILADO BANCOS")
    ingresos = pd.read_excel(xls, "INGRESOS XML")
    egresos = pd.read_excel(xls, "EGRESOS XML")
    comp_ing = pd.read_excel(xls, "COMPLEMENTOS INGRESOS XML")
    comp_egr = pd.read_excel(xls, "COMPLEMENTOS EGRESOS XML")

    bancos['fecha'] = pd.to_datetime(bancos['fecha'], errors='coerce')
    ingresos['FechaEmisionXML'] = pd.to_datetime(ingresos['FechaEmisionXML'], errors='coerce')
    egresos['FechaEmisionXML'] = pd.to_datetime(egresos['FechaEmisionXML'], errors='coerce')
    comp_ing['FechaPago'] = pd.to_datetime(comp_ing['FechaPago'], errors='coerce')
    comp_egr['FechaPago'] = pd.to_datetime(comp_egr['FechaPago'], errors='coerce')

    conciliados_ing1, no_conc_ing = [], []
    conciliados_egr1, no_conc_egr = [], []

    # --- FASE 1: Conciliación directa ---
    for _, row in ingresos.iterrows():
        ventana = bancos[
            (bancos['fecha'] >= row['FechaEmisionXML']) &
            (bancos['fecha'] <= row['FechaEmisionXML'] + pd.DateOffset(months=3)) &
            (bancos['cargos'].isna())
        ]
        match = ventana[abs(ventana['abonos'] - row['Total']) <= 1]
        if not match.empty:
            conciliados_ing1.append(row)
        else:
            no_conc_ing.append(row)

    for _, row in egresos.iterrows():
        ventana = bancos[
            (bancos['fecha'] >= row['FechaEmisionXML']) &
            (bancos['fecha'] <= row['FechaEmisionXML'] + pd.DateOffset(months=3)) &
            (bancos['abonos'].isna())
        ]
        match = ventana[abs(ventana['cargos'] - row['Total']) <= 1]
        if not match.empty:
            conciliados_egr1.append(row)
        else:
            no_conc_egr.append(row)

    df_no_conc_ing = pd.DataFrame(no_conc_ing)
    df_no_conc_egr = pd.DataFrame(no_conc_egr)

    # --- FASE 2: Complementos de ingreso/egreso ---
    conciliados_ing2, conciliados_egr2 = [], []

    for uuid, grupo in comp_ing.groupby('UUID'):
        fecha = grupo['FechaPago'].iloc[0]
        imp = grupo['ImpPagado'].sum()
        folios = grupo['folio relacionado'].dropna().unique()
        relacionados = df_no_conc_ing[df_no_conc_ing['Folio'].isin(folios)]
        if relacionados.empty:
            continue
        ventana = bancos[
            (bancos['fecha'] >= fecha) &
            (bancos['fecha'] <= fecha + pd.DateOffset(months=3)) &
            (bancos['cargos'].isna())
        ]
        combinacion = buscar_combinaciones(ventana, 'abonos', imp)
        if not combinacion.empty:
            conciliados_ing2.append({
                'UUID': uuid,
                'FechaPago': fecha.date(),
                'ImpPagado': imp,
                'Folios': ', '.join(folios)
            })

    for uuid, grupo in comp_egr.groupby('UUID'):
        fecha = grupo['FechaPago'].iloc[0]
        imp = grupo['ImpPagado'].sum()
        folios = grupo['FolioRel'].dropna().unique()
        relacionados = df_no_conc_egr[df_no_conc_egr['Folio'].isin(folios)]
        if relacionados.empty:
            continue
        ventana = bancos[
            (bancos['fecha'] >= fecha) &
            (bancos['fecha'] <= fecha + pd.DateOffset(months=3)) &
            (bancos['abonos'].isna())
        ]
        combinacion = buscar_combinaciones(ventana, 'cargos', imp)
        if not combinacion.empty:
            conciliados_egr2.append({
                'UUID': uuid,
                'FechaPago': fecha.date(),
                'ImpPagado': imp,
                'Folios': ', '.join(folios)
            })

    # Exportar todo a Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        pd.DataFrame(conciliados_ing1).to_excel(writer, "F1 INGRESOS CONCILIADOS", index=False)
        df_no_conc_ing.to_excel(writer, "F1 INGRESOS NO CONCILIADOS", index=False)
        pd.DataFrame(conciliados_ing2).to_excel(writer, "F2 INGRESOS COMP CONC", index=False)

        pd.DataFrame(conciliados_egr1).to_excel(writer, "F1 EGRESOS CONCILIADOS", index=False)
        df_no_conc_egr.to_excel(writer, "F1 EGRESOS NO CONCILIADOS", index=False)
        pd.DataFrame(conciliados_egr2).to_excel(writer, "F2 EGRESOS COMP CONC", index=False)

        bancos.to_excel(writer, "COMPILADO BANCOS", index=False)
        ingresos.to_excel(writer, "INGRESOS XML", index=False)
        egresos.to_excel(writer, "EGRESOS XML", index=False)
        comp_ing.to_excel(writer, "COMPLEMENTOS INGRESOS XML", index=False)
        comp_egr.to_excel(writer, "COMPLEMENTOS EGRESOS XML", index=False)

    output.seek(0)
    return output
