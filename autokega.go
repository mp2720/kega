package main

import (
    "os/exec"
    "math/rand"
    "fmt"
    "sync"
)

const WORKERS = 10
const START = 0
const KEGA_PATH = "./kega.py"

func doVar(num int) {
    time := rand.Int() % 120 + 120
    cmd := exec.Command(KEGA_PATH, "-y", fmt.Sprintf("-M%v", time), fmt.Sprint(num))
    cmd.Output()
    fmt.Println(num)
}

var vars chan int
var wg sync.WaitGroup

func varsToChan() {
    defer wg.Done()
    for i:=START; i<100000; i++ {
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

func main() {
    vars =  make(chan int, 100)
    wg.Add(1)
    go varsToChan()

    for i:=0; i<WORKERS; i++ {
        wg.Add(1)
        go worker()
    }
    wg.Wait()
}
