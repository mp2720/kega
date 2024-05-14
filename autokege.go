package main

import (
    "os/exec"
    "math/rand"
    "fmt"
    "sync"
)

func doVar(num int) {
    time := rand.Int()%120 + 120
    cmd := exec.Command("kega", "-y", fmt.Sprintf("-M%v", time), fmt.Sprint(num))
    cmd.Output()
    fmt.Println(num)
}

var vars chan int
var wg sync.WaitGroup

func varsToChan() {
    start := 4000
    defer wg.Done()
    for i:=start; i<100000; i++ {
        vars<-(25000000+i)
    }
    close(vars)
}

func worker() {
    defer wg.Done()
    for {
        num, open := <-vars
        if open == false {
            break
        }
        doVar(num)
    }
}

var THREADS = 10
var START = 4000

func main() {
    vars =  make(chan int, 100)
    wg.Add(1)
    go varsToChan()

    workers := 10
    for i:=0; i<workers; i++ {
        wg.Add(1)
        go worker()
    }
    wg.Wait()
}