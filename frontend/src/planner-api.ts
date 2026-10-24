import {apiError} from './api';

export const departments = ['Passenger Services', 'Ramp Operations', 'Fuel Services'] as const;
export type Department = typeof departments[number];
export type Scenario = 'Low' | 'Medium' | 'High';
export type DemandHour = {hour:number; aircraft:number; passengers:number; fuel_requests:number};
export type Upload = {name:string; rows:DemandHour[]};
export type Settings = {
  scenario:Scenario; multiplier:number; seed:number;
  scenario_multipliers:Record<Scenario,number>;
  service_minutes:Record<Department,number>; service_wages:Record<Department,number>;
  staffing_minimums:Record<Department,number>; target_utilization:Record<Department,number>;
  shift_hours:number; break_minutes:number; max_weekly_hours:number; minimum_rest_hours:number; worker_pool_size:number;
};
export type Disruption = {absences:number; surge_percent:number; service_delay_percent:number; disruption_day:number; disruption_start:number; disruption_hours:number};
export const noDisruption:Disruption = {absences:0,surge_percent:0,service_delay_percent:0,disruption_day:5,disruption_start:15,disruption_hours:4};
export const defaultDisruption:Disruption = {...noDisruption,absences:2,surge_percent:50,service_delay_percent:25};
export const defaultSettings:Settings = {
  scenario:'Medium',multiplier:1,seed:42,scenario_multipliers:{Low:1.15,Medium:1.4,High:1.7},
  service_minutes:{'Passenger Services':5,'Ramp Operations':24,'Fuel Services':30},
  service_wages:{'Passenger Services':26,'Ramp Operations':32,'Fuel Services':35},
  staffing_minimums:{'Passenger Services':1,'Ramp Operations':2,'Fuel Services':1},
  target_utilization:{'Passenger Services':.8,'Ramp Operations':.8,'Fuel Services':.8},
  shift_hours:8,break_minutes:30,max_weekly_hours:40,minimum_rest_hours:8,worker_pool_size:30,
};
export type Metrics = {
  workers:number; shifts:number; scheduled_labor_hours:number; estimated_labor_cost:number;
  demand_seat_hours:number; uncovered_seat_hours:number; coverage_percent:number; unfilled_roster_slots:number;
  departments:{department:Department;workers:number;shifts:number;uncovered_seat_hours:number;unfilled_roster_slots:number;absent_workers:number}[];
};
export type Shift = {employee_id:string;department:Department;day:number;start_hour:number;end_hour:number;week_start_hour:number;week_end_hour:number;break_start:number;break_end:number;break_minutes:number};
export type Roster = {metrics:Metrics;shifts:Shift[]};
export type Plan = {
  baseline:Roster;proposed:Roster;provenance:string;
  simulation:{forecast:DemandHour[];ordinary_forecast:DemandHour[];requirements:{hour:number;department:Department;required:number;workload_minutes:number}[];
    training_report:null|{train_rows:number;test_rows:number;metrics:Record<string,{mae:number;baseline_mae:number}>}};
  scenario_summary:{ordinary_total_aircraft:number;scenarios:{scenario:Scenario;total_aircraft:number;peak_aircraft_per_hour:number;peak_seats:Record<Department,number>;event_multiplier:number}[]};
};
export type Decision = {id:number;manager:string;notes:string;approved:boolean;timestamp:string;scope:string;[key:string]:unknown};

export function payload(settings:Settings,upload:Upload|null,disruption:Disruption) {
  const {shift_hours,break_minutes,max_weekly_hours,minimum_rest_hours,worker_pool_size,...inputs}=settings;
  return {inputs:{...inputs,include_queue_options:false,forecast_mode:upload?'uploaded':'trained',
    ...(upload?{ordinary_demand:upload.rows,source_name:upload.name}:{})},
    shift_hours,break_minutes,max_weekly_hours,minimum_rest_hours,worker_pool_size,...disruption};
}
export async function post<T>(endpoint:string,body:unknown):Promise<T> {
  const response=await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(!response.ok)throw await apiError(response,endpoint);
  return response.json() as Promise<T>;
}
export const getPlan=(settings:Settings,upload:Upload|null,disruption:Disruption)=>post<Plan>('/api/staffing-plan',payload(settings,upload,disruption));
