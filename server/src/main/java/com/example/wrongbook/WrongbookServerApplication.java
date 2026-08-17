package com.example.wrongbook;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class WrongbookServerApplication {

	public static void main(String[] args) {
		SpringApplication.run(WrongbookServerApplication.class, args);
	}

}
