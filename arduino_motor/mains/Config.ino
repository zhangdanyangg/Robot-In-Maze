#include "Config.h"
int const Config::MAX_SPEED_ANALOG = 255;
int const Config::DESIGNED_MAX_SPEED = 400;
int const Config::WHEEL_DIAMETER = 6;
int const Config::COUNTS_PER_REVOLUTION = 2249/2;
double const Config::DISTANCE_PER_TICK_CM = (PI*WHEEL_DIAMETER)/COUNTS_PER_REVOLUTION; //0.016762077012005334
int const Config::SAMPLE_TIME = 10;
double const Config::WHEELS_INTERVAL = 17.18; // turn left, slightly overturn

double Config::MAX_SPEED = 300;
double Config::TARGET_SPEED = 200;
double Config::MIN_SPEED = 100;
double Config::PID_UPPER_LIMIT = COUNTS_PER_REVOLUTION*6*(double(MAX_SPEED)/DESIGNED_MAX_SPEED);
double Config::PID_LOWER_LIMIT = PID_UPPER_LIMIT*(double(MIN_SPEED)/DESIGNED_MAX_SPEED);
double Config::PID_SETPOINT = PID_UPPER_LIMIT*(double(TARGET_SPEED)/DESIGNED_MAX_SPEED);

double const Config::TICKS_PER_DEGREE = (WHEELS_INTERVAL/2)*(PI/180)*(1/DISTANCE_PER_TICK_CM);