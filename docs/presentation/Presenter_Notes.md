# CrewPilot AI — presenter notes

Six slides. About three minutes. The Track 1 brief does not set a pitch length; this is a compact rehearsal script.

## 1. Staff the rush
CrewPilot addresses Track 1, The Intelligent FBO. Our focus is staffing. The prototype helps an FBO manager compare a normal week with event demand, inspect staffing needs, and test disruptions. It is planning support. A person keeps final authority.

## 2. One arrival, several jobs
An aircraft may create ramp, fuel, and customer-service work. Fuel is only added when requested. The task times and crew counts shown are configurable demo assumptions. They are not validated FBO standards. When arrivals overlap, qualified coverage matters more than a single total headcount.

## 3. Plan the full week
The browser planner compares a synthetic ordinary week with three event cases across seven days. Low, medium, and high use fixed multipliers of 1.15, 1.4, and 1.7. Those are scenario inputs, not forecasts. The model translates estimated work into role and shift coverage.

## 4. Stress-test the plan
The simulator can add four unexpected aircraft, remove two ramp workers, and delay three expected arrivals by up to 45 minutes. It shows uncovered tasks under the disruption. The original plan and the recovery proposal face the same affected work.

## 5. Manager decides
The weekly planner builds shift coverage using peak hourly need, then assigns eligible fictional workers with a greedy rule. It checks the configured hours, rest, breaks, and qualifications. It is not a proven global optimizer. The manager reviews, approves, or rejects. Nothing is dispatched.

## 6. What comes next
The current demo uses synthetic arrivals, tasks, and workers. It has no validated Van Nuys or Los Angeles FBO demand data. So it cannot claim real-world forecast accuracy or proven operational savings. Next: validate the task model with an FBO operator, obtain approved historical demand, back-test forecasts, then measure uncovered work and labor tradeoffs.
