local M = {}
local utils = require("utils")
local fzf = require("fzf")

require("fzf").default_options = {
    window_on_create = function()
        vim.cmd("set winhl=Normal:Normal")
    end
}

SERVER_PID = -1
PYTHON = "python"
PLUGIN_DIR = debug.getinfo(1).source:sub(2):match('^(.*)/lua/[^/]+$')
CURL = "curl"
RG = "rg"

local function start_server()
    if SERVER_PID > 0 then
        os.execute("kill " .. SERVER_PID)
    end
    local s_server = utils.create_server()
    local f_server = utils.create_server()
    local _, server_port = s_server:getsockname(); s_server:close()
    local _, fzf_port = f_server:getsockname(); f_server:close()
    local pid = utils.spawn(PYTHON, { PLUGIN_DIR .. "/python/internal_server.py", ".", server_port, fzf_port })
    SERVER_PID = pid
    return server_port, fzf_port
end

local function get_file_filter_option(file_filter)
    --assert file_filter in ("default", "uuu")
    if file_filter == "default" then
        return ""
    elseif file_filter == "uuu" then
        return "-uuu"
    else
        return "--" .. file_filter
    end
end

local function get_rg_command(d, file_filter)
    file_filter = file_filter or "default"

    local commands = {}
    table.insert(commands, RG)
    table.insert(commands, get_file_filter_option(file_filter))
    table.insert(commands, "--color always")
    table.insert(commands, "--line-number")
    table.insert(commands, "^")
    table.insert(commands, d)

    local result = {}
    for _, v in ipairs(commands) do
        if #v > 0 then
            table.insert(result, v)
        end
    end

    return table.concat(result, " ")
end

local function option_to_shell_string(key, value)
    if value == true then
        return "--" .. key
    elseif utils.is_array(value) then
        local strs = {}
        for _, v in ipairs(value) do
            --assert "'" not in str(v), f"Invalid option was specified: {v}"
            table.insert(strs, "--" .. key .. " '" .. v .. "'")
        end
        return table.concat(strs, " ")
    else
        --assert "'" not in str(value), f"Invalid option was specified: {value}"
        return "--" .. key .. " '" .. value .. "'"
    end
end


local function options_to_shell_string(options)
    local arr = {}
    for k, v in pairs(options) do
        table.insert(arr, option_to_shell_string(k, v))
    end
    return arr
end

local function get_fzf_options_core(query, server_port)
    local options = {
        multi = true,
        ansi = true,
        query = query,
        bind = {
            'alt-u:execute-silent(curl "http://localhost:' .. server_port .. '?origin_move=up")',
            'alt-p:execute-silent(curl "http://localhost:' .. server_port .. '?origin_move=back")',
            'alt-n:execute-silent(curl "http://localhost:' .. server_port .. '?file_filter=default")',
            'alt-l:execute-silent(curl "http://localhost:' .. server_port .. '?file_filter=uuu")',
        },
    }
    return table.concat(options_to_shell_string(options), " ")
end

local function get_fzf_options_view(abs_dir)
    return ("--reverse " ..
        "--header '%s' " ..
        "--delimiter ':' " ..
        "--preview 'bat --color always --highlight-line {2} {1}' " ..
        "--preview-window 'down' " ..
        "--preview-window '+{2}'"):format(abs_dir)
end

local function get_fzf_options(d, query, server_port)
    local abs_dir = utils.get_absdir_view(d)
    return table.concat({ get_fzf_options_core(query, server_port), get_fzf_options_view(abs_dir), }, " ")
end

local function get_fzf_dict(d, query, server_port)
    return { options = get_fzf_options(d, query, server_port) }
end

local function get_command_json(origin, a_query, server_port)
    local rg_command = get_rg_command(origin)
    local fzf_dict = get_fzf_dict(origin, a_query, server_port)
    return { rg_command = rg_command, fzf_dict = fzf_dict }
end

local function execute_fzf(rg_command_, fzf_dict, fzf_port)
    local options_ = "--listen " .. fzf_port .. " " .. fzf_dict["options"]
    coroutine.wrap(function(rg_command, options)
        local results = fzf.fzf(rg_command, options)
        os.execute("kill " .. SERVER_PID)
        for _, result in ipairs(results) do
            local sp = utils.split(result, ":")
            local path, line_n = sp[1], sp[2]
            vim.api.nvim_command("edit " .. path)
            vim.api.nvim_command("normal " .. line_n .. 'Gzz')
        end
    end)(rg_command_, options_)
end

local function call(a_query)
    vim.api.nvim_set_var("fzf_layout", { window = 'enew' })

    local server_port, fzf_port = start_server()
    local command_json = get_command_json(".", a_query, server_port)

    local rg_command = command_json["rg_command"]
    local fzf_dict = command_json["fzf_dict"]
    execute_fzf(rg_command, fzf_dict, fzf_port)
end

M.run = function(a_query)
    call(a_query)
end

return M
