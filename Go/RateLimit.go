package rate

import "time"

type Limit struct {
    count   int
    expires time.Time
}

type Rule struct {
    CountMultiplier float32
    CountAddend     int
}

// string key is the identifier for rule to match on,
// e.g. "127.0.0.1", "admin", etc
type Rules map[string]Rule

type RateLimitMgr struct {
    instances     map[string]*Limit
    max_actions   int
    time_interval time.Duration
    custom_rules  Rules
}

func NewRateLimitMgr(actions int, interval time.Duration, rules Rules) *RateLimitMgr {
    return &RateLimitMgr{
        instances:     make(map[string]*Limit),
        max_actions:   actions,
        time_interval: interval,
        custom_rules:  rules,
    }
}

func (m *RateLimitMgr) Check(identifier string) bool {
    var now = time.Now()
    var multiplier float32 = 1.0
    var addend = 0

    // was there an custom rule for this identifier?
    if m.custom_rules != nil {
        if _, ok := m.custom_rules[identifier]; ok {
            multiplier = m.custom_rules[identifier].CountMultiplier
            addend = m.custom_rules[identifier].CountAddend
        }
    }

    if _, ok := m.instances[identifier]; !ok {
        // identifier does not exist, create new entry
        m.instances[identifier] = &Limit{
            count:   1,
            expires: now.Add(m.time_interval),
        }
        go m.Cleanup(identifier)

        // allow action
        return true
    }

    if m.instances[identifier].count > int(float32(m.max_actions)*multiplier)+addend {
        // actions are full, need to wait for timeout
        return false
    }

    // increments and allow with new expires timer
    m.instances[identifier].count = m.instances[identifier].count + 1

    return true
}

func (m *RateLimitMgr) Cleanup(identifier string) {
    var expires = m.instances[identifier].expires
    time.Sleep(time.Until(expires))
    delete(m.instances, identifier)
}