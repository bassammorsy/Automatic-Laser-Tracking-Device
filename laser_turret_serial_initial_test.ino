#include <Servo.h>

const int panPin  = 3;
const int tiltPin = 4;
const int laserPin = 2;

Servo panServo;
Servo tiltServo;

void setup() {
  Serial.begin(9600);
  pinMode(laserPin, OUTPUT);

  panServo.attach(panPin);
  tiltServo.attach(tiltPin);

  panServo.write(90);
  tiltServo.write(90);
  digitalWrite(laserPin, LOW);
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    // Format: P<angle>  T<angle>  LON  LOFF
    if (cmd.startsWith("P")) {
      int angle = constrain(cmd.substring(1).toInt(), 0, 180);
      panServo.write(angle);
    }
    else if (cmd.startsWith("T")) {
      int angle = constrain(cmd.substring(1).toInt(), 20, 160);
      tiltServo.write(angle);
    }
    else if (cmd == "LON")  { digitalWrite(laserPin, HIGH); }
    else if (cmd == "LOFF") { digitalWrite(laserPin, LOW);  }
  }
}