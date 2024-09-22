        try:
            if data.startswith("Throttle"):
                # Split the data by commas
                parts = data.split(",")

                # Ensure that there are enough parts to parse
                if len(parts) >= 7:
                    # Extract each value
                    throttle_str = parts[0].replace("Throttle", "").strip()
                    rpm_str = parts[1].split(":")[1].strip()
                    # pulse_count_str = parts[2].split(":")[1].strip()  # Not used currently
                    thrust_str = parts[3].split(":")[1].strip()
                    current_str = parts[4].split(":")[1].strip()
                    ambient_temp_str = parts[5].split(":")[1].strip()
                    object_temp_str = parts[6].split(":")[1].strip()

                    # Convert to appropriate types
                    throttle = float(throttle_str)
                    rpm = int(rpm_str)
                    thrust = float(thrust_str)
                    current = float(current_str)
                    ambient_temp = float(ambient_temp_str)
                    object_temp = float(object_temp_str)

                    # Update the labels in the GUI
                    # Accessing the measurement display boxes correctly
                    self.measurements_layout.itemAt(0).layout().itemAt(0).widget().setText(f"{thrust:.2f} g")
                    self.measurements_layout.itemAt(1).layout().itemAt(0).widget().setText(f"{rpm}")
                    self.measurements_layout.itemAt(2).layout().itemAt(0).widget().setText(f"{current:.2f} A")
                    self.measurements_layout.itemAt(3).layout().itemAt(0).widget().setText(f"{ambient_temp:.1f} °C")
                    self.measurements_layout.itemAt(4).layout().itemAt(0).widget().setText(f"{object_temp:.1f} °C")

                    # Optionally, update plots here
                    # For example:
                    # self.current_plot.update_plot(current)
                    # self.thrust_plot.update_plot(throttle, thrust)

                else:
                    print(f"Incomplete data received: {data}")
            elif "Motor speed adjusted to" in data:
                speed_str = data.split("to")[-1].strip().rstrip("%")
                try:
                    speed = int(speed_str)
                    self.speed_label.setText(f"Motor Speed: {speed}%")
                except ValueError:
                    print(f"Invalid speed value: {speed_str}")
            elif data == "Motor stopped":
                self.speed_label.setText("Motor Speed: 0%")
            elif data == "Stopping motor gradually":
                self.speed_label.setText("Motor Speed: Stopping...")
            elif any(keyword in data for keyword in ["Initializing", "IR Sensor Test", "Calibrating", "Voltage offset", "Current offset"]):
                print(f"Setup message: {data}")
            else:
                print(f"Unhandled data: {data}")
        except Exception as e:
            print(f"Error parsing data '{data}': {e}")
