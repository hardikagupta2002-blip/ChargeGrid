import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class ChargeGridDataEngine:
    def __init__(self):
        # Master list of operational cities mapped to your frontend configuration
        self.cities = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Pune", "Kolkata", "New York", "Los Angeles", "San Francisco"]
        self.port_types = ["Level 2", "DC Fast", "Supercharger"]
        self.statuses = ["Online", "Busy", "Offline", "Error"]
        
        # Fixed coordinates for map visualization
        self.city_coords = {
            "Mumbai": (19.0760, 72.8777),
            "Delhi": (28.7041, 77.1025),
            "Bangalore": (12.9716, 77.5946),
            "Hyderabad": (17.3850, 78.4867),
            "Chennai": (13.0827, 80.2707),
            "Pune": (18.5204, 73.8567),
            "Kolkata": (22.5726, 88.3639),
            "New York": (40.7128, -74.0060),
            "Los Angeles": (34.0522, -118.2437),
            "San Francisco": (37.7749, -122.4194)
        }
        
        # Vehicle pool for simulated active session logs
        self.vehicles = ["Tesla Model 3", "Tesla Model Y", "Hyundai Ioniq 5", "Kia EV6", "Tata Nexon EV", "Mahindra XUV400", "Audi e-tron", "Porsche Taycan"]

    def get_all_data(self, selected_cities: tuple, selected_port_types: tuple, days: int) -> dict:
        """
        Generates and filters all analytical data structures needed by app.py.
        Uses deterministic random seeds based on the current minute to ensure 
        data mutates realistically during real-time dashboard refreshes.
        """
        # Ensure inputs are lists for calculation purposes
        cities = list(selected_cities) if selected_cities else self.cities
        port_types = list(selected_port_types) if selected_port_types else self.port_types
        
        # Use minute-based seeding so data "shifts" smoothly across refresh intervals
        current_time = datetime.now()
        seed = current_time.minute + current_time.hour * 60
        rng = np.random.default_rng(seed)
        
        # 1. Generate Station Infrastructure Topology
        stations_list = []
        station_id_counter = 1
        for city in cities:
            lat_center, lon_center = self.city_coords.get(city, (20.0, 75.0))
            # Generate 3 to 6 stations per city
            num_stations = rng.integers(3, 7)
            for i in range(num_stations):
                # Scatter stations slightly around the city center
                lat = lat_center + rng.uniform(-0.08, 0.08)
                lon = lon_center + rng.uniform(-0.08, 0.08)
                
                p_type = rng.choice(port_types)
                total_ports = int(rng.integers(4, 16))
                status = rng.choice(self.statuses, p=[0.70, 0.18, 0.07, 0.05])
                
                active_sessions = 0
                if status == "Busy":
                    active_sessions = int(total_ports * rng.uniform(0.7, 1.0))
                elif status == "Online":
                    active_sessions = int(total_ports * rng.uniform(0.1, 0.6))
                
                kw_today = active_sessions * rng.uniform(30, 90) + rng.uniform(100, 500)
                
                stations_list.append({
                    "station_id": f"STN-{station_id_counter:03d}",
                    "name": f"{city} {p_type} Hub {i+1}",
                    "city": city,
                    "port_type": p_type,
                    "lat": lat,
                    "lon": lon,
                    "total_ports": total_ports,
                    "active_sessions": active_sessions,
                    "kw_today": kw_today,
                    "status": status
                })
                station_id_counter += 1
                
        df_stations = pd.DataFrame(stations_list)
        
        # Early exit structure if data drops to zero due to aggressive filtering
        if df_stations.empty:
            return self._empty_response()

        # 2. Compile Port Distribution Count Calculations
        status_counts = df_stations.groupby("status")["total_ports"].sum().to_dict()
        for s in self.statuses:
            status_counts.setdefault(s, 0)
            
        total_ports = sum(status_counts.values())
        error_ports = status_counts["Error"] + status_counts["Offline"]
        active_sessions_total = int(df_stations["active_sessions"].sum())
        
        # 3. Generate Historical & Forecast Time-Series Metrics
        base_kw_per_day = len(df_stations) * 350
        dates = [current_time.date() - timedelta(days=x) for x in range(days - 1, -1, -1)]
        
        trend_rows = []
        for d in dates:
            # Introduce a weekly seasonality factor (weekends see higher utilization)
            weekday_factor = 1.2 if d.weekday() >= 5 else 0.95
            random_noise = rng.uniform(0.85, 1.15)
            
            day_kw = base_kw_per_day * weekday_factor * random_noise
            day_sessions = int(day_kw / rng.uniform(22, 28))
            
            trend_rows.append({
                "date": d.strftime("%Y-%m-%d"),
                "kw": day_kw,
                "sessions": day_sessions
            })
        df_trend = pd.DataFrame(trend_rows)
        
        # 4. Generate 24-Hour Peak Load Aggregations
        hourly_rows = []
        # Typical EV curve: Double peak load at morning commutes and late evening returns
        hourly_distribution = [
            0.15, 0.10, 0.08, 0.05, 0.07, 0.15, 0.40, 0.75, 
            0.90, 0.85, 0.70, 0.65, 0.60, 0.58, 0.62, 0.70, 
            0.85, 0.95, 1.00, 0.90, 0.75, 0.55, 0.35, 0.22
        ]
        for hour in range(24):
            factor = hourly_distribution[hour] * rng.uniform(0.9, 1.1)
            hourly_rows.append({
                "hour": f"{hour:02d}:00",
                "kw": (base_kw_per_day / 15) * factor
            })
        df_hourly = pd.DataFrame(hourly_rows)
        
        # 5. Extract City and Port Type Regional Aggregations
        df_city_kw = df_stations.groupby("city")["kw_today"].sum().reset_index().rename(columns={"kw_today": "kw"})
        df_city_kw = df_city_kw.sort_values(by="kw", ascending=False)
        
        # 6. Dynamic Event Alert Engine Modeling
        alerts = []
        critical_stations = df_stations[df_stations["status"] == "Error"].take(range(3), is_axis=False)
        for _, row in critical_stations.iterrows():
            alerts.append({
                "level": "critical",
                "title": "Hardware Communication Failure",
                "message": f"Station baseline connectivity dropped at {row['name']}. Critical fault detected in telemetry array.",
                "time": (current_time - timedelta(minutes=int(rng.integers(5, 45)))).strftime("%H:%M")
            })
            
        warning_stations = df_stations[df_stations["status"] == "Offline"].take(range(3), is_axis=False)
        for _, row in warning_stations.iterrows():
            alerts.append({
                "level": "warning",
                "title": "Grid Power Curtailment",
                "message": f"Local utility load shedding forced automation cutoff at {row['name']}.",
                "time": (current_time - timedelta(minutes=int(rng.integers(12, 120)))).strftime("%H:%M")
            })

        # 7. Simulated Live Individual Session Logs
        session_rows = []
        session_counter = 1024
        for _, stn in df_stations.iterrows():
            # Build current active sessions
            for _ in range(stn["active_sessions"]):
                duration = rng.uniform(10, 180)
                kw_now = rng.uniform(30, 150) if stn["port_type"] != "Level 2" else rng.uniform(7, 22)
                kw_del = (duration / 60) * kw_now * rng.uniform(0.9, 0.98)
                
                session_rows.append({
                    "session_id": f"CG-{session_counter}",
                    "port_id": f"P-{rng.integers(1, stn['total_ports'] + 1)}",
                    "city": stn["city"],
                    "port_type": stn["port_type"],
                    "status": "Active",
                    "kw_now": kw_now,
                    "kw_delivered": kw_del,
                    "duration_min": duration,
                    "vehicle": rng.choice(self.vehicles),
                    "started": (current_time - timedelta(minutes=int(duration))).strftime("%H:%M")
                })
                session_counter += 1
                
            # Build historic context within the same log pool (Completed, Aborted, or Error states)
            for _ in range(int(rng.integers(1, 4))):
                hist_status = rng.choice(["Completed", "Completed", "Aborted", "Error"], p=[0.75, 0.15, 0.05, 0.05])
                duration = rng.uniform(20, 120)
                kw_del = rng.uniform(15, 85)
                
                session_rows.append({
                    "session_id": f"CG-{session_counter}",
                    "port_id": f"P-{rng.integers(1, stn['total_ports'] + 1)}",
                    "city": stn["city"],
                    "port_type": stn["port_type"],
                    "status": hist_status,
                    "kw_now": 0.0,
                    "kw_delivered": kw_del,
                    "duration_min": duration,
                    "vehicle": rng.choice(self.vehicles),
                    "started": (current_time - timedelta(hours=int(rng.integers(1, 6)))).strftime("%H:%M")
                })
                session_counter += 1
        df_sessions = pd.DataFrame(session_rows)

        # 8. Individual Component Level Port Health Diagnostics
        health_rows = []
        port_id_global = 5001
        for _, stn in df_stations.iterrows():
            for p in range(1, int(stn["total_ports"]) + 1):
                is_flagged = rng.choice([True, False], p=[0.06, 0.94])
                err_count = int(rng.integers(3, 8)) if is_flagged else int(rng.integers(0, 3))
                success_rate = rng.uniform(65, 88) if is_flagged else rng.uniform(94, 100)
                
                health_rows.append({
                    "port_id": f"PRT-{port_id_global}",
                    "station_name": stn["name"],
                    "city": stn["city"],
                    "port_type": stn["port_type"],
                    "success_rate": success_rate,
                    "error_count": err_count,
                    "avg_kw": rng.uniform(45, 120) if stn["port_type"] != "Level 2" else rng.uniform(6, 15),
                    "last_error": (current_time - timedelta(days=int(rng.integers(0, 4)))).strftime("%d %b %H:%M"),
                    "flagged": is_flagged
                })
                port_id_global += 1
        df_health = pd.DataFrame(health_rows)

        # 9. Port Infrastructure Rolling 7-Day Error Trends
        error_trend_rows = []
        for d in dates:
            for pt in port_types:
                error_trend_rows.append({
                    "date": d.strftime("%Y-%m-%d"),
                    "port_type": pt,
                    "errors": int(rng.integers(1, 12)) if pt == "Supercharger" else int(rng.integers(0, 6))
                })
        df_error_trend = pd.DataFrame(error_trend_rows)

        # 10. Matrix Utilization Optimization Heatmap
        heatmap_data = np.zeros((7, 24))
        for row_idx in range(7):
            for col_idx in range(24):
                base = base_kw_per_day / 24
                h_factor = hourly_distribution[col_idx]
                w_factor = 1.2 if row_idx >= 5 else 0.9
                heatmap_data[row_idx, col_idx] = base * h_factor * w_factor * rng.uniform(0.8, 1.2)
        df_heatmap = pd.DataFrame(heatmap_data)

        # 11. Predictive Forecast Demand Array
        forecast_rows = []
        # Append historical references first
        for _, r in df_trend.iterrows():
            forecast_rows.append({"date": r["date"], "kw": r["kw"], "lower": r["kw"], "upper": r["kw"], "type": "historical"})
            
        # Append 7-day algorithmic extension
        last_date = current_time.date()
        for i in range(1, 8):
            f_date = last_date + timedelta(days=i)
            w_factor = 1.25 if f_date.weekday() >= 5 else 0.95
            predicted_value = base_kw_per_day * w_factor * rng.uniform(1.02, 1.08) # Models a modest network growth trajectory
            
            forecast_rows.append({
                "date": f_date.strftime("%Y-%m-%d"),
                "kw": predicted_value,
                "lower": predicted_value * 0.90,
                "upper": predicted_value * 1.10,
                "type": "forecast"
            })
        df_forecast = pd.DataFrame(forecast_rows)

        # 12. Segmented Dynamic Monetary Metrics
        revenue_by_type = []
        for pt in port_types:
            mult = 0.45 if pt == "Supercharger" else (0.30 if pt == "DC Fast" else 0.18)
            revenue_by_type.append({
                "port_type": pt,
                "revenue": df_trend["kw"].iloc[-1] * mult * (len(df_stations[df_stations["port_type"] == pt]) / len(df_stations))
            })
        df_revenue_type = pd.DataFrame(revenue_by_type)

        # 13. System Structural Duration Characteristics
        duration_by_city = []
        for c in cities:
            duration_by_city.append({
                "city": c,
                "avg_duration": rng.uniform(45, 95) if c in ["Mumbai", "New York", "Delhi"] else rng.uniform(30, 65)
            })
        df_duration_city = pd.DataFrame(duration_by_city)

        # Final Compiled Data Frame State Package Structure
        today_kw_total = df_trend["kw"].iloc[-1]
        today_rev_total = df_revenue_type["revenue"].sum()

        return {
            "kpis": {
                "total_kw": today_kw_total,
                "active_sessions": active_sessions_total,
                "total_ports": total_ports,
                "error_ports": error_ports,
                "revenue": today_rev_total,
                "kw_delta": float(rng.uniform(-5, 12)),
                "port_delta": float(rng.uniform(-1, 2)),
                "rev_delta": float(rng.uniform(-4, 15))
            },
            "stations": df_stations,
            "port_status_counts": status_counts,
            "daily_trend": df_trend,
            "hourly_kw": df_hourly,
            "city_kw": df_city_kw,
            "alerts": alerts,
            "live_sessions": df_sessions,
            "port_health": df_health,
            "error_trend": df_error_trend,
            "heatmap": df_heatmap,
            "forecast": df_forecast,
            "revenue_by_type": df_revenue_type,
            "duration_by_city": df_duration_city
        }

    def _empty_response(self) -> dict:
        """Fallback framework prevents structural template failure during filter drop events."""
        return {
            "kpis": {"total_kw": 0, "active_sessions": 0, "total_ports": 0, "error_ports": 0, "revenue": 0},
            "stations": pd.DataFrame(), "port_status_counts": {}, "daily_trend": pd.DataFrame(columns=["date", "kw", "sessions"]),
            "hourly_kw": pd.DataFrame(columns=["hour", "kw"]), "city_kw": pd.DataFrame(columns=["city", "kw"]), "alerts": [],
            "live_sessions": pd.DataFrame(), "port_health": pd.DataFrame(), "error_trend": pd.DataFrame(),
            "heatmap": pd.DataFrame(), "forecast": pd.DataFrame(), "revenue_by_type": pd.DataFrame(), "duration_by_city": pd.DataFrame()
        }
