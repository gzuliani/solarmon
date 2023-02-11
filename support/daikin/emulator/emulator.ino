// Basic emulator of a Daikin Altherma heat pump

static const int NO_DATA_RATIO   = 10; // percent
static const int CAN_ERROR_RATIO =  1; // percent
static const char* HEADLINE = "Daikin Altherma Emulator v.0.1\r";

static const int buffer_length = 256;
static char buffer[buffer_length];
int i = 0;

char random_hex_digit() {
  int value = random(16);
  return value < 10 ? '0' + value : 'A' - 10 + value;
}

void setup() {
  Serial.begin(38400);
}

void loop() {

  while (Serial.available() > 0) {

    char c = Serial.read();

    if ((c == ' ') || (c == '\n'))
      continue;

    buffer[i] = toupper(c);
    i = ++i % buffer_length;

    if (c != '\r')
      continue;

    buffer[i] = 0x00;
    i = 0;

    if (random(100) < CAN_ERROR_RATIO) {
      Serial.print("CAN ERROR\r");
    } else if (random(100) < NO_DATA_RATIO) {
      Serial.print("NO DATA\r");
    } else if (strcmp(buffer, "ATZ\r") == 0) {
      delay(1000);
      Serial.print(HEADLINE);
    } else if (strcmp(buffer, "ATWS\r") == 0) {
      Serial.print(HEADLINE);
    } else if (strncmp(buffer, "AT", 2) == 0) {
      Serial.print("OK\r");
    } else if (strlen(buffer) == 15) {
      buffer[1] = '2'; // response mark
      int value_pos = 6;
      const int value_length = 4;
      if ((buffer[4] == 'F') && (buffer[5] == 'A'))
        value_pos += 4;
      for (int i = 0; i < value_length; i++)
        buffer[value_pos + i] = random_hex_digit();
      Serial.print(buffer);
    } else {
      Serial.print("CAN ERROR\r");
    }
    Serial.print(">");
  }
}
