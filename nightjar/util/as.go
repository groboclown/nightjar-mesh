package util


func AsStr(v *string) string {
	if v == nil {
		return "<nil>"
	}
	return *v
}

func AsInt64(v *int64) int64 {
	if v == nil {
		return -9999
	}
	return *v
}
