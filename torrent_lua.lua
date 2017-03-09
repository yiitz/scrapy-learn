function main(splash)
  local proxyidx = 1
  local retry = 1
  splash:on_request(function(request)
      request:set_timeout(150)
      if splash.args.proxys and #splash.args.proxys >= proxyidx then
        if retry == 10 then
            --proxyidx =  proxyidx+1
            retry = 1
        end
        retry = retry + 1
        local p = splash.args.proxys[proxyidx]
        print('retry: '..p)
        local pp = stringsplit(p,':')
        request:set_proxy{
              host = pp[1],
              port = pp[2],
              type = 'HTTP'
          }
      end
    end)
  --splash.js_enabled=false
  if splash.args.clearcookie then
    splash:clear_cookies()
    splash.args.cookies = {}
  elseif splash.args.cookies then
    splash:init_cookies(splash.args.cookies)
  end
  local ok,reason=splash:go{
  splash.args.url,
  headers=splash.args.headers,
  http_method=splash.args.http_method,
  body=splash.args.body,
  }
  
  if not ok then
    -- splash.js_enabled=true
    -- splash:go{
      -- splash.args.url,
      -- headers=splash.args.headers,
      -- http_method=splash.args.http_method,
      -- body=splash.args.body,
      -- }
    splash:wait(10)
  end
  local retry_times = 6
  for a=2,retry_times,1 do
    local entries = splash:history()
    if entries and entries[#entries] then
      local last_response = entries[#entries].response
        if last_response.ok then
            local proxytmp = nil
            if splash.args.proxys and proxyidx > 2 then
            proxytmp = splash.args.proxys[proxyidx-1]
          end
          return {
            url = splash:url(),
            headers = last_response.headers,
            http_status = last_response.status,
            cookies = splash:get_cookies(),
            html = splash:html()
            --p = proxytmp
          }
        end 
    end
    splash:go{
      splash.args.url,
      headers=splash.args.headers,
      http_method=splash.args.http_method,
      body=splash.args.body,
      }
    splash:wait(12)
  end
  error('failed to request url.')
end
function print_r ( t )  
    local print_r_cache={}
    local function sub_print_r(t,indent)
        if (print_r_cache[tostring(t)]) then
            print(indent.."*"..tostring(t))
        else
            print_r_cache[tostring(t)]=true
            if (type(t)=="table") then
                for pos,val in pairs(t) do
                    if (type(val)=="table") then
                        print(indent.."["..pos.."] => "..tostring(t).." {")
                        sub_print_r(val,indent..string.rep(" ",string.len(pos)+8))
                        print(indent..string.rep(" ",string.len(pos)+6).."}")
                    elseif (type(val)=="string") then
                        print(indent.."["..pos..'] => "'..val..'"')
                    else
                        print(indent.."["..pos.."] => "..tostring(val))
                    end
                end
            else
                print(indent..tostring(t))
            end
        end
    end
    if (type(t)=="table") then
        print(tostring(t).." {")
        sub_print_r(t,"  ")
        print("}")
    else
        sub_print_r(t,"  ")
    end
    print()
end
function stringsplit(s, p)
    local rt= {}
    string.gsub(s, '[^'..p..']+', function(w) table.insert(rt, w) end )
    return rt
end
