# Weather Forecasts & Flight Planner Execution Plan

## Requirements
- Full backend/frontend test coverage
- Flight planner between KPAO and 7S5 (terrain, VFR, fuel stops, overlays)
- Weather overlays must work and be tested
- Airport info must be cached, weather fetched live
- All code/tests/scripts must run **only in containers** (no host artifacts)
- Makefile/scripts must enforce containerization

## Task List
- [x] Inventory endpoints and tests
- [x] Implement backend flight planner (Dijkstra)
- [x] Add `/api/plan_route` endpoint
- [x] Write backend test for KPAO-7S5
- [ ] Fix frontend test (app context issue)
- [ ] Add frontend integration for planning a route (UI + test)
- [ ] Validate Makefile/scripts for strict containerization
- [ ] Ensure all tests pass in container

## Notes
- All future work must maintain containerization.
- This file is the canonical plan for this project.
