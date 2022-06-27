from idr_client.configs import config
# flake8: noqa

extract_data = f'''select 
       d.DOB,
       d.Gender,
       d.unique_patient_no                                                                 as CCC,
       d.patient_id                                                                        as PatientPK,
       timestampdiff(year, d.DOB, hiv.visit_date)                                          as AgeEnrollment,
       timestampdiff(year, d.DOB, reg.art_start_date)                                      as AgeARTStart,
       timestampdiff(year, d.DOB, reg.latest_vis_date)                                     as AgeLastVisit,
       i.siteCode                                                                          as SiteCode,
       i.FacilityName                                                                      as FacilityName,
       CAST(coalesce(date_first_enrolled_in_care, min(hiv.visit_date)) as Date)            as RegistrationDate,
       case max(hiv.entry_point)
           when 160542 then 'OPD'
           when 160563 then 'Other'
           when 160539 then 'VCT'
           when 160538 then 'PMTCT'
           when 160541 then 'TB'
           when 160536 then 'IPD - Adult'
           else ''
           end                                                                             as PatientSource,
       mid(min(concat(hiv.visit_date, hiv.date_started_art_at_transferring_facility)), 11) as PreviousARTStartDate,
       reg.date_started_art_this_facility                                                  as StartARTAtThisFAcility,
       least(ifnull(mid(min(concat(hiv.visit_date, hiv.date_started_art_at_transferring_facility)), 11),
                    reg.date_started + interval rand()*1000 year), reg.date_started)       as StartARTDate,
       reg.PreviousARTUse                                                                  as PreviousARTUse,
       reg.PreviousARTPurpose                                                              as PreviousARTPurpose,
       reg.PreviousARTRegimen                                                              as PreviousARTRegimen,
       reg.DateLastUsed                                                                    as DateLastUsed,
       reg.regimen                                                                         as StartRegimen,
       reg.regimen_line                                                                    as StartRegimenLine,
       case
           when reg.latest_vis_date is not null then reg.latest_vis_date
           else reg.last_art_date end                                                        as LastARTDate,
       reg.last_regimen                                                                    as LastRegimen,
       reg.last_regimen_line                                                               as LastRegimenLine,
       reg.latest_tca                                                                      as ExpectedReturn,
       reg.latest_vis_date                                                                 as LastVisit,
       timestampdiff(month, reg.art_start_date, reg.latest_vis_date)                       as Duration,
       disc.ExitDate                                                                       as ExitDate,
       disc.ExitReason                                                                     as ExitReason,
       hiv.date_created                                                                    as Date_Created,
       GREATEST(
               COALESCE(hiv.date_last_modified, disc.date_last_modified, reg.date_last_modified),
               COALESCE(disc.date_last_modified, reg.date_last_modified, hiv.date_last_modified),
               COALESCE(reg.date_last_modified, hiv.date_last_modified, disc.date_last_modified)
           )                                                                               as Date_Last_Modified
from {config.etl_db_name}.etl_hiv_enrollment hiv
         join {config.etl_db_name}.etl_patient_demographics d on d.patient_id = hiv.patient_id
         left outer join (select d.patient_id,
                                 coalesce(max(date(d.effective_discontinuation_date)),
                                          max(date(d.visit_date)))as ExitDate,
                                 (case d.discontinuation_reason
                                      when 159492 then 'Transfer Out'
                                      when 160034 then 'Died'
                                      when 5240 then 'LTFU'
                                      when 819 then 'Stopped Treatment'
                                      else'' end)                   as ExitReason,
                                 max(d.date_last_modified)        as date_last_modified
                          from {config.etl_db_name}.etl_patient_program_discontinuation d
                          where d.program_name = 'HIV'
                          group by d.patient_id) disc on disc.patient_id = hiv.patient_id
         left outer join (select e.patient_id,
                                 min(e.date_started)                                              as art_start_date,
                                 min(e.date_started)                                              as date_started_art_this_facility,
                                 e.date_started,
                                 e.gender,
                                 e.dob,
                                 d.ExitDate                                                       as dis_date,
                                 if(d.ExitDate is not null, 1, 0)                                 as TOut,
                                 e.regimen,
                                 e.regimen_line,
                                 e.alternative_regimen,
                                 max(fup.next_appointment_date)                                   as latest_tca,
                                 last_art_date,
                                 last_regimen,
                                 last_regimen_line,
                                 if(enr.transfer_in_date is not null, 1, 0)                       as TIn,
                                 case enr.previous_art_use when 1 then 'Yes' when 0 then 'No' end as PreviousARTUse,
                                 enr.previous_art_purpose                                         as PreviousARTPurpose,
                                 enr.previous_art_regimen                                         as PreviousARTRegimen,
                                 ''                                                               as DateLastUsed,
                                 max(fup.visit_date)                                              as latest_vis_date,
                                 e.date_created,
                                 e.date_last_modified
                          from (select e.patient_id,
                                       p.dob,
                                       p.Gender,
                                       min(e.date_started)                                             as date_started,
                                       max(e.date_started)                                             as last_art_date,
                                       mid(min(concat(e.date_started, e.regimen_name)), 11)            as regimen,
                                       mid(min(concat(e.date_started, e.regimen_line)), 11)            as regimen_line,
                                       mid(max(concat(e.date_started, e.regimen_name)), 11)            as last_regimen,
                                       mid(max(concat(e.date_started, e.regimen_line)), 11)            as last_regimen_line,
                                       max(if(discontinued, 1, 0))as                                      alternative_regimen,
                                       GREATEST(COALESCE(p.date_created, ph.date_created),
                                                COALESCE(ph.date_created, p.date_created))             as date_created,
                                       GREATEST(COALESCE(p.date_last_modified, ph.date_last_modified),
                                                COALESCE(ph.date_last_modified, p.date_last_modified)) as date_last_modified,
                                       e.provider                                                      as provider
                                from {config.etl_db_name}.etl_drug_event e
                                         join {config.etl_db_name}.etl_patient_demographics p on p.patient_id = e.patient_id
                                         left join {config.etl_db_name}.etl_pharmacy_extract ph
                                                   on ph.patient_id = e.patient_id and is_arv = 1
                                where e.program = 'HIV'
                                group by e.patient_id) e
                                   left outer join (select d.patient_id,
                                                           coalesce(max(date(d.effective_discontinuation_date)),
                                                                    max(date(d.visit_date))) ExitDate
                                                    from {config.etl_db_name}.etl_patient_program_discontinuation d
                                                    where d.program_name = 'HIV'
                                                    group by d.patient_id)d on d.patient_id = e.patient_id
                                   inner join (select e.patient_id                                           as patient_id,
                                                      mid(max(concat(e.visit_date, e.transfer_in_date)), 11) as transfer_in_date,
                                                      case mid(max(concat(e.visit_date, e.arv_status)), 11)
                                                          when 1 then 'Yes'
                                                          when 0
                                                              then 'No' end                                as previous_art_use,
                                                      concat_ws('|', NULLIF(
                                                              case mid(max(concat(pre.visit_date, pre.PMTCT)), 11)
                                                                  when 1065 then 'PMTCT' end, ''),
                                                                NULLIF(case mid(max(concat(pre.visit_date, pre.PEP)), 11)
                                                                           when 1 then 'PEP' end, ''),
                                                                NULLIF(case mid(max(concat(pre.visit_date, pre.PrEP)), 11)
                                                                           when 1065 then 'PrEP' end, ''),
                                                                NULLIF(case mid(max(concat(pre.visit_date, pre.HAART)), 11)
                                                                           when 1185 then 'HAART' end, '')
                                                          )                                                  as previous_art_purpose,
                                                      concat_ws('|', NULLIF(
                                                              case mid(max(concat(pre.visit_date, pre.PMTCT_regimen)), 11)
                                                                  when 164968 then 'AZT/3TC/DTG'
                                                                  when 164969 then 'TDF/3TC/DTG'
                                                                  when 164970 then 'ABC/3TC/DTG'
                                                                  when 164505 then 'TDF-3TC-EFV'
                                                                  when 792 then 'D4T/3TC/NVP'
                                                                  when 160124 then 'AZT/3TC/EFV'
                                                                  when 160104 then 'D4T/3TC/EFV'
                                                                  when 161361 then 'EDF/3TC/EFV'
                                                                  when 104565 then 'EFV/FTC/TDF'
                                                                  when 162201 then '3TC/LPV/TDF/r'
                                                                  when 817 then 'ABC/3TC/AZT'
                                                                  when 162199 then 'ABC/NVP/3TC'
                                                                  when 162200 then '3TC/ABC/LPV/r'
                                                                  when 162565 then '3TC/NVP/TDF'
                                                                  when 1652 then '3TC/NVP/AZT'
                                                                  when 162561 then '3TC/AZT/LPV/r'
                                                                  when 164511 then 'AZT-3TC-ATV/r'
                                                                  when 164512 then 'TDF-3TC-ATV/r'
                                                                  when 162560 then '3TC/D4T/LPV/r'
                                                                  when 162563 then '3TC/ABC/EFV'
                                                                  when 162562 then 'ABC/LPV/R/TDF'
                                                                  when 162559 then 'ABC/DDI/LPV/r' end, ''),
                                                                NULLIF(
                                                                        case mid(max(concat(pre.visit_date, pre.PEP_regimen)), 11)
                                                                            when 164968 then 'AZT/3TC/DTG'
                                                                            when 164969 then 'TDF/3TC/DTG'
                                                                            when 164970 then 'ABC/3TC/DTG'
                                                                            when 164505 then 'TDF-3TC-EFV'
                                                                            when 792 then 'D4T/3TC/NVP'
                                                                            when 160124 then 'AZT/3TC/EFV'
                                                                            when 160104 then 'D4T/3TC/EFV'
                                                                            when 1652 then '3TC/NVP/AZT'
                                                                            when 161361 then 'EDF/3TC/EFV'
                                                                            when 104565 then 'EFV/FTC/TDF'
                                                                            when 162201 then '3TC/LPV/TDF/r'
                                                                            when 817 then 'ABC/3TC/AZT'
                                                                            when 162199 then 'ABC/NVP/3TC'
                                                                            when 162200 then '3TC/ABC/LPV/r'
                                                                            when 162565 then '3TC/NVP/TDF'
                                                                            when 162561 then '3TC/AZT/LPV/r'
                                                                            when 164511 then 'AZT-3TC-ATV/r'
                                                                            when 164512 then 'TDF-3TC-ATV/r'
                                                                            when 162560 then '3TC/D4T/LPV/r'
                                                                            when 162563 then '3TC/ABC/EFV'
                                                                            when 162562 then 'ABC/LPV/R/TDF'
                                                                            when 162559 then 'ABC/DDI/LPV/r' end, ''),
                                                                NULLIF(
                                                                        case mid(max(concat(pre.visit_date, pre.PrEP_regimen)), 11)
                                                                            when 164968 then 'AZT/3TC/DTG'
                                                                            when 164969 then 'TDF/3TC/DTG'
                                                                            when 164970 then 'ABC/3TC/DTG'
                                                                            when 164505 then 'TDF-3TC-EFV'
                                                                            when 792 then 'D4T/3TC/NVP'
                                                                            when 160124 then 'AZT/3TC/EFV'
                                                                            when 160104 then 'D4T/3TC/EFV'
                                                                            when 161361 then 'EDF/3TC/EFV'
                                                                            when 104565 then 'EFV/FTC/TDF'
                                                                            when 162201 then '3TC/LPV/TDF/r'
                                                                            when 817 then 'ABC/3TC/AZT'
                                                                            when 162199 then 'ABC/NVP/3TC'
                                                                            when 162200 then '3TC/ABC/LPV/r'
                                                                            when 162565 then '3TC/NVP/TDF'
                                                                            when 1652 then '3TC/NVP/AZT'
                                                                            when 162561 then '3TC/AZT/LPV/r'
                                                                            when 164511 then 'AZT-3TC-ATV/r'
                                                                            when 164512 then 'TDF-3TC-ATV/r'
                                                                            when 162560 then '3TC/D4T/LPV/r'
                                                                            when 162563 then '3TC/ABC/EFV'
                                                                            when 162562 then 'ABC/LPV/R/TDF'
                                                                            when 162559 then 'ABC/DDI/LPV/r' end, ''),
                                                                NULLIF(
                                                                        case mid(max(concat(pre.visit_date, pre.HAART_regimen)), 11)
                                                                            when 164968 then 'AZT/3TC/DTG'
                                                                            when 164969 then 'TDF/3TC/DTG'
                                                                            when 164970 then 'ABC/3TC/DTG'
                                                                            when 164505 then 'TDF-3TC-EFV'
                                                                            when 792 then 'D4T/3TC/NVP'
                                                                            when 160124 then 'AZT/3TC/EFV'
                                                                            when 160104 then 'D4T/3TC/EFV'
                                                                            when 161361 then 'EDF/3TC/EFV'
                                                                            when 104565 then 'EFV/FTC/TDF'
                                                                            when 162201 then '3TC/LPV/TDF/r'
                                                                            when 817 then 'ABC/3TC/AZT'
                                                                            when 162199 then 'ABC/NVP/3TC'
                                                                            when 162200 then '3TC/ABC/LPV/r'
                                                                            when 162565 then '3TC/NVP/TDF'
                                                                            when 1652 then '3TC/NVP/AZT'
                                                                            when 162561 then '3TC/AZT/LPV/r'
                                                                            when 164511 then 'AZT-3TC-ATV/r'
                                                                            when 164512 then 'TDF-3TC-ATV/r'
                                                                            when 162560 then '3TC/D4T/LPV/r'
                                                                            when 162563 then '3TC/ABC/EFV'
                                                                            when 162562 then 'ABC/LPV/R/TDF'
                                                                            when 162559 then 'ABC/DDI/LPV/r' end, '')
                                                          )                                                  as previous_art_regimen
                                               from {config.etl_db_name}.etl_hiv_enrollment e
                                                        left join {config.etl_db_name}.etl_pre_hiv_enrollment_art pre
                                                                  on e.visit_id = pre.visit_id and e.patient_id = pre.patient_id
                                               group by e.patient_id) enr on enr.patient_id = e.patient_id
                                   left outer join {config.etl_db_name}.etl_patient_hiv_followup fup
                                                   on fup.patient_id = e.patient_id
                          group by e.patient_id)reg on reg.patient_id = hiv.patient_id
         join {config.etl_db_name}.etl_default_facility_info i
where d.unique_patient_no is not null
group by d.patient_id
having min(hiv.visit_date) is not null
   and StartARTDate is not null;
'''