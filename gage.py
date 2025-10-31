import streamlit as st
import pandas as pd
from db import get_qry

consulta = """
                SELECT StatusName, L.LocationName AREA, LO.LocationName LINEA, Gage_SN, GageDescriptionName DESCRIPCION,
                       G.Notes NOTAS  
                  FROM Gages G LEFT JOIN GageDescriptions ON GageDescription_RID = GageDescription_RID_FK
                               LEFT JOIN Locations L ON L.Location_RID = StorageLocation_RID_FK
                               LEFT JOIN Locations LO ON LO.Location_RID = CurrentLocation_RID_FK
                               LEFT JOIN Custodians ON Custodian_RID = L.Custodian_RID_FK
                               LEFT JOIN GageTypes ON GageType_RID = GageType_RID_FK
                               LEFT JOIN Status S ON S.Status_RID = Status_RID_FK
                 WHERE Gage_ID = ?;
           """

consultaCalibra = """
                    SELECT ActionType, Gage_SN, RecurrenceOptionType OPCION, (CAST(Period AS nvarchar(3)) + '  ' + RecurrenceType) [FRECUENCIA CALIBRACION],
                           LastDone, NextDue  
                      FROM ActionSchedules LEFT JOIN GageCalibrations ON ActionSchedule_RID = ActionSchedule_RID_FK
                                           LEFT JOIN Gages G ON Gage_RID_FK = Gage_RID      
                     WHERE Gage_ID = ?;
           """

consultaMsa = """
                    SELECT ActionType, Gage_SN, RecurrenceOptionType OPCION, (CAST(Period AS nvarchar(3)) + '  ' + RecurrenceType) [FRECUENCIA MSA],
                           LastDone, NextDue  
                      FROM ActionSchedules LEFT JOIN GageMsaActivities ON ActionSchedule_RID_FK = ActionSchedule_RID
                                           LEFT JOIN Gages G ON Gage_RID_FK = Gage_RID      
                     WHERE Gage_ID = ?;
           """

class Gage:
    def __init__(self, general=None, calibracion=None, msa=None):
        self.general = general
        self.calibracion = calibracion
        self.msa = msa

    def render(self):
        import streamlit as st
        st.markdown("### Información General del Gage")
        if self.general is not None:
            st.dataframe(self.general, use_container_width=True)
        else:
            st.info("Sin datos generales.")

        st.markdown("### Calibraciones")
        if self.calibracion is not None:
            st.dataframe(self.calibracion, use_container_width=True)
        else:
            st.info("Sin datos de calibración.")

        st.markdown("### Estudios MSA")
        if self.msa is not None:
            st.dataframe(self.msa, use_container_width=True)
        else:
            st.info("Sin datos de MSA.")


def ExecuteQry(param):
    try:
        # --- Consulta principal ---
        rows, description = get_qry(consulta, [param])
        df_general = None
        if rows:
            df_general = pd.DataFrame.from_records(rows, columns=[desc[0] for desc in description])

        # --- Consulta de Calibración ---
        rows, description = get_qry(consultaCalibra, [param])
        df_calibra = None
        if rows:
            df_calibra = pd.DataFrame.from_records(rows, columns=[desc[0] for desc in description])

        # --- Consulta de MSA ---
        rows, description = get_qry(consultaMsa, [param])
        df_msa = None
        if rows:
            df_msa = pd.DataFrame.from_records(rows, columns=[desc[0] for desc in description])

        # --- Crear y devolver el objeto Gage ---
        gage = Gage(
            general=df_general,
            calibracion=df_calibra,
            msa=df_msa
        )
        return gage

    except Exception as e:
        st.error(f"Ocurrió un error: {str(e)}")
        return None
