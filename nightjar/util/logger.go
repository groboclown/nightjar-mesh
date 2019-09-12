package util


import (
	"log"
)

const (
	DEBUG		= 1
	VERBOSE		= 2
	WARN		= 3
)

var LogLevel int = WARN

func SetLogLevel(level int) {
	LogLevel = level
}

func Debug(v ...interface{}) {
	if LogLevel <= DEBUG {
		log.Println(append([](interface{}){"DEBUG - "}, v...))
	}
}

func Debugf(format string, v ...interface{}) {
	if LogLevel <= DEBUG {
		log.Printf("DEBUG - " + format, v...)
	}
}

func Log(v ...interface{}) {
	if LogLevel <= VERBOSE {
		log.Println(append([](interface{}){"VERBOSE - "}, v...))
	}
}

func Logf(format string, v ...interface{}) {
	if LogLevel <= VERBOSE {
		log.Printf("VERBOSE - " + format, v...)
	}
}

func Warn(v ...interface{}) {
	if LogLevel <= WARN {
		log.Println(append([](interface{}){"!!! "}, v...))
	}
}

func Warnf(format string, v ...interface{}) {
	if LogLevel <= WARN {
		log.Printf("!!! " + format, v...)
	}
}

func Error(v ...interface{}) {
	log.Panic(v...)
}

func Errorf(format string, v ...interface{}) {
	log.Panicf(format, v...)
}

func Fatal(v ...interface{}) {
	log.Fatal(v...)
}

func Fatalf(format string, v ...interface{}) {
	log.Fatalf(format, v...)
}
