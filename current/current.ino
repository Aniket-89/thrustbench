void setup()
{
  Serial.begin(9600);
}

void loop()
{
  int readA0 = analogRead(A0);
  int current = (readA0 - 505) * 78 / 512;
  Serial.println(readA0);
  Serial.println(current);
  delay(666);
}