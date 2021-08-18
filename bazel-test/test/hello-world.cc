#include <ctime>
#include <string>
#include <iostream>

std::string get_greet(const std::string& who) {
  return "Hello to" + who;
}

void print_localtime() {
  std::time_t result = std::time(nullptr);
  std::cout << "Local time =>" << std::asctime(std::localtime(&result));
  std::cout << std::endl;
}

int main(int argc, char** argv) {
  std::string who = "world";
  if (argc > 1) {
    who = argv[1];
  }
  std::cout << get_greet(who) << std::endl;
  print_localtime();
  return 0;
}

