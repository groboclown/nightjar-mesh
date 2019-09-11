package util


type Any interface {
}


func AssertNotNil(val Any) {
    if val == nil {
        panic("Code logic asserts value must be non-nil, but found nil value.")
    }
}

func AssertNil(val Any) {
    if val != nil {
        panic("Code logic asserts value must be nil, but found non-nil value.")
    }
}
