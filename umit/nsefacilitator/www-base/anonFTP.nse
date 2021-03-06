id="Anonymous FTP"

description="Checks to see if a FTP server allows anonymous logins"

author = "Eddie Bell <ejlbell@gmail.com>"

license = "See nmaps COPYING for licence"

categories = {"intrusive"}

require "shortport"

portrule = shortport.port_or_service(21, "ftp")

action = function(host, port)
	local socket = nmap.new_socket()
	local result
	local status = true
	local isAnon = false

	local err_catch = function()
		socket:close()
	end

	local try = nmap.new_try(err_catch())

	socket:set_timeout(5000)
	try(socket:connect(host.ip, port.number, port.protocol))
       	try(socket:send("USER anonymous\n\r"))
	try(socket:send("PASS IEUser@\n\r"))

        while status do
		status, result = socket:receive_lines(1);
		if string.match(result, "^230") then
			isAnon = true
			break
		end
	end

	socket:close()

	if(isAnon) then
		return "FTP: Anonymous login allowed"
	end
end
