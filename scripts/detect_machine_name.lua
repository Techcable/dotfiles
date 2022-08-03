#!/usr/bin/env luajit

function parseString(raw_text)
    local quote_style = string.match(raw_text, "^[\"']")
    if quote_style == nil then
        error(string.format("String must start with either `'` or `\"`: %q", raw_text))
    end
    -- Verify ending quote exists and matches start
    do
        local quote_end = string.match(raw_text, "[\"']")
        if quote_end ~= quote_style then
            error(string.format("String must end with `%s` (like it began): %q", quote_style, raw_text))
        end
    end
    local text = string.sub(raw_text, 2, -2)
    local res = string.match(text, [[^([%w%s_%-%.%?%:]*)$]])
    if res ~= nil then
        return res
    else
        -- TODO: Include original quote_style in message?
        error(string.format("Unable to parse into string: %q", text))
    end
end

function detectMachineName(stream)
    local res = {count = 0}
    for l in stream:lines() do
        res.count = res.count + 1
        local short, val = string.match(l, [[export%("MACHINE_NAME(_?%a*)", ([^)]+)%)]])
        if val ~= nil then
            val = parseString(val)
            if short == "_SHORT" then
                res.short = val
            elseif short == "" then
                res.long = val
            else
                assert(short ~= nil) -- Should not happen
                -- Ignore
            end
        end
    end
    return res
end

function warning(msg)
    io.stderr:write("WARNING: ", msg, '\n')
end

function fatal(msg)
    io.stderr:write("ERROR: ", msg, '\n')
    os.exit(false)
end

local opts = {
    mode = "long",
    quiet = false,
    verbose = false,
    config_file_name = nil,
}


-- parse options
do
    local parser = {
        args = arg,
        idx = 1,
    }
    function parser:next()
        if self.idx <= #self.args then
            local res = self.args[self.idx]
            self.idx = self.idx + 1
            return res
        else
            return nil
        end
    end
    function attrSetter(attr, value)
        return function()
            opts[attr] = value
        end
    end
    local table = {
        ["--short"] = attrSetter("mode", "short"),
        ["--long"] = attrSetter("mode", "long"),
        ["--verbose"] = attrSetter("verbose", true),
        ["--quiet"] = attrSetter("quiet", true),
        ["--config"] = function()
            opts.config_file_name = parser:next() or fatal("Must sepecify path after --config")
        end,
        ["--help"] = function()
            print("Usage: ./detect_machine_name.lua [OPTIONS]")
            print()
            print("Available options:")
            print()
            print("--config [path]    Override the config file to analyse")
            print("--long             Detects the \"long\" machine name (default)")
            print("--short            Detects the \"short\" machine name")
            print("                   Falls back to long name if not found (with warning)")
            print("--quiet, -q        Suppress all warning messages")
            print("--verbose, -v      Print even more verbose messages")
            print("--help             Prints this help message")
            os.exit()
        end,
    }
    -- aliases
    table["-q"] = table["--quiet"]
    table["-v"] = table["--verbose"]
    -- parse loop
    while true do
        local opt = parser:next()
        if opt == nil then break end
        local func = table[opt]
        if func ~= nil then
            func()
        else
            fatal("Unknown argument/option: " .. opt)
        end
    end
end
if opts.config_file_name == nil then
    local homedir = os.getenv("HOME") or fatal("Unable to detect $HOME directory")
    opts.config_file_name = homedir .. '/.shell-config.py'
end

if opts.verbose then
    io.stderr:write("Analysing file: ", opts.config_file_name, "\n")
end

local config_file, errmsg = io.open(opts.config_file_name, "r")
if not config_file then
    fatal(string.format("Unable to open config file %q: %s", config_file_name, errmsg))
end
local res = detectMachineName(config_file)
config_file:close()

if res[opts.mode] ~= nil then
    print(res[opts.mode])
elseif res.long ~= nil then
    assert(opts.mode ~= "long")
    if not opts.quiet then
        warning(string.format("Unable to detect `%s` name, using long one instead", opts.mode))
    end
    print(res.long)
else
    fatal("Unable to detect machine name!")
end
