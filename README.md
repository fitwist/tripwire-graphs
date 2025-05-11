API опубликован на render.com.

# При тестировании 
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"team_solving_x2": 0, "stakeholders_solving_x2": 6, "approach_solving_x2": 6, "planning_solving_x2": 6, "measurement_solving_x2": 6, "risks_solving_x2": 6, "team_tools": 3, "stakeholders_tools": 11, "approach_tools": 11, "planning_tools": 11, "measurement_tools": 11, "risks_tools": 11}' \
  --output static/sample.jpeg \
  https://tripwire-graphs.onrender.com/chart/
```