import streamlit as st
from db import get_qry
from datetime import datetime

consulta = """
                SELECT StatusName, L.LocationName Area, LO.LocationName Linea, Gage_SN, GageDescriptionName Descripcion,
                       G.Notes Notas  
                  FROM Gages G LEFT JOIN GageDescriptions ON GageDescription_RID = GageDescription_RID_FK
                               LEFT JOIN Locations L ON L.Location_RID = StorageLocation_RID_FK
                               LEFT JOIN Locations LO ON LO.Location_RID = CurrentLocation_RID_FK
                               LEFT JOIN Custodians ON Custodian_RID = L.Custodian_RID_FK
                               LEFT JOIN GageTypes ON GageType_RID = GageType_RID_FK
                               LEFT JOIN Status S ON S.Status_RID = Status_RID_FK
                 WHERE Gage_ID = ?;
           """

consultaCalibra = """
                    SELECT ActionType, Gage_SN, RecurrenceOptionType OPCION, (CAST(Period AS nvarchar(3)) + '  ' + RecurrenceType) FRECUENCIA,
                           LastDone, NextDue  
                      FROM ActionSchedules LEFT JOIN GageCalibrations ON ActionSchedule_RID = ActionSchedule_RID_FK
                                           LEFT JOIN Gages G ON Gage_RID_FK = Gage_RID      
                     WHERE Gage_ID = ?;
           """

consultaMsa = """
                    SELECT ActionType, Gage_SN, RecurrenceOptionType OPCION, (CAST(Period AS nvarchar(3)) + '  ' + RecurrenceType) FRECUENCIA,
                           LastDone, NextDue  
                      FROM ActionSchedules LEFT JOIN GageMsaActivities ON ActionSchedule_RID_FK = ActionSchedule_RID
                                           LEFT JOIN Gages G ON Gage_RID_FK = Gage_RID      
                     WHERE Gage_ID = ?;
           """

# Función auxiliar para formatear fechas
def fmt_date(value):
    if not value:
        return ""
    
    if isinstance(value, str):
        # Intentar convertir la cadena a datetime si viene como texto
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value  # Si no se puede convertir, devuelve el texto tal cual
    return value.strftime("%Y/%m/%d")       

# =====================================================
# CLASES
# =====================================================
class Calibration:
    def __init__(self, action_type, gage_sn, recurrence, frecuencia, last_done, next_due):
        self.action_type = action_type
        self.gage_sn = gage_sn
        self.recurrence = recurrence
        self.frecuencia = frecuencia
        self.last_done = fmt_date(last_done)
        self.next_due = fmt_date(next_due)

    def dias_para_proximo(self):
        """Retorna los días restantes hasta la próxima calibración."""
        try:
            # Detectar si es datetime o string
            if isinstance(self.next_due, datetime):
                fecha = self.next_due
            else:
                # Intentar varios formatos comunes
                for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
                    try:
                        fecha = datetime.strptime(str(self.next_due), fmt)
                        break
                    except ValueError:
                        fecha = None
                if fecha is None:
                    return None

            # Calcular diferencia
            dias = (fecha - datetime.now()).days
            return dias

        except Exception:
            return None

class Msa:
    def __init__(self, action_type, gage_sn, recurrence, frecuencia, last_done, next_due):
        self.action_type = action_type
        self.gage_sn = gage_sn
        self.recurrence = recurrence
        self.frecuencia = frecuencia
        self.last_done = fmt_date(last_done)
        self.next_due = fmt_date(next_due)

    def dias_para_proximo(self):
        """Retorna los días restantes hasta la próxima calibración."""
        try:
            # Detectar si es datetime o string
            if isinstance(self.next_due, datetime):
                fecha = self.next_due
            else:
                # Intentar varios formatos comunes
                for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
                    try:
                        fecha = datetime.strptime(str(self.next_due), fmt)
                        break
                    except ValueError:
                        fecha = None
                if fecha is None:
                    return None

            # Calcular diferencia
            dias = (fecha - datetime.now()).days
            return dias

        except Exception:
            return None

class Gage:
    def __init__(self, estatus, area, linea, operacion, descripcion, nota, calibration=None, msa=None):
        """
        Inicializa un gage con datos individuales y opcionalmente un objeto Calibration y Msa.
        """
        self.estatus = estatus
        self.area = area
        self.linea = linea
        self.operacion = operacion
        self.descripcion = descripcion
        self.nota = nota
        self.calibration = calibration or Recurrence()  # Evita None
        self.msa = msa  or Recurrence()  # Evita None

class Recurrence:
    def __init__(self, action_type=None, frecuencia=None, last_done=None, next_due=None):
        self.action_type = action_type
        self.frecuencia = frecuencia
        self.last_done = last_done
        self.next_due = next_due

    def dias_para_proximo(self):
        """Calcula días restantes a la próxima acción"""
        from datetime import datetime
        if not self.next_due:
            return None
        try:
            fecha = datetime.strptime(str(self.next_due), "%Y-%m-%d")
            return (fecha - datetime.today()).days
        except Exception:
            return None    

def row_to_dict(rows, description):
    if not rows:
        return None
    cols = [desc[0] for desc in description]
    return dict(zip(cols, rows[0]))


def ExecuteQry(db: str, param):
    try:
        # --- Consulta principal ---
        row = row_to_dict(*get_qry(db, consulta, [param]))
        if not row:
            return None

        # --- Consulta de Calibración ---
        rows, description = get_qry(db, consultaCalibra, [param])
        cal_obj = None
        if rows:
            cols = [desc[0] for desc in description]
            cal_row = dict(zip(cols, rows[0]))
            cal_obj = Calibration(
                action_type=cal_row.get("ActionType"),
                gage_sn=cal_row.get("Gage_SN"),
                recurrence=cal_row.get("OPCION"),
                frecuencia=cal_row.get("FRECUENCIA"),
                last_done=cal_row.get("LastDone"),
                next_due=cal_row.get("NextDue"),
            )            

        # --- Consulta de MSA ---
        rows, description = get_qry(db, consultaMsa, [param])
        msa_obj = None
        if rows:
            cols = [desc[0] for desc in description]
            msa_row = dict(zip(cols, rows[0]))
            msa_obj = Msa(
                action_type=msa_row.get("ActionType"),
                gage_sn=msa_row.get("Gage_SN"),
                recurrence=msa_row.get("OPCION"),
                frecuencia=msa_row.get("FRECUENCIA"),
                last_done=msa_row.get("LastDone"),
                next_due=msa_row.get("NextDue"),
            )

        # --- Crear objeto principal Gage ---
        gage = Gage(
            estatus=row.get("StatusName"),
            area=row.get("Area"),
            linea=row.get("Linea"),
            operacion=row.get("Gage_SN"),
            descripcion=row.get("Descripcion"),
            nota=row.get("Notas"),
            calibration=cal_obj,
            msa=msa_obj,
        )         

        return gage

    except Exception as e:
        st.error(f"Ocurrió un error: {str(e)}")
        return None
