###################################
# Nov.11, 2019 - HA 0.101.3的兼容性
# Mar.29, 2019 - 修复风速导致的无法开机问题
###################################

from miio.airconditioningcompanion import *
#from miio.click_common import command, format_output, EnumType
_LOGGER = logging.getLogger(__name__)
# Command templates per model number (f.e. 0180111111)
# [po], [mo], [wi], [sw], [tt], [tt1], [tt4] and [tt7] are markers which will be replaced
DEVICE_COMMAND_TEMPLATES = {
    'fallback': {
        'deviceType': 'generic',
        'base': '[po][mo][wi][sw][tt][li]'
    },
    '0100010727': {
        'deviceType': 'gree_2',
        'base': '[po][mo][wi][sw][tt][li]00[wtw][pmp][tt1]205002102000[tt2]0[wtw][pmp][tt1]2070020000[wbw]0[tt3]',
        
        'extra': {
            'tt1': {
                'Auto': 9
            },
           
            'tt2': {                
                'Heat': 10,
                'Dehumidify': 8,
                'Cool': 7,
                'Auto': 14,
                'Ventilate': 9,
                # 'Off': 9
            },
            
            'tt3': {
                'Heat': 7,
                'Dehumidify': 6,
                'Cool': 4,
                'Auto': 11,
                'Ventilate': 6
            },
            'pmp': {
                'Off': '00',
                'Cool': '90',
                'Heat': 'C0',
                'Auto': '80',
                'Ventilate': 'B0',
                'Dehumidify': 'A0'
            },
            'wbw': {
                'Low': 1,
                'Medium': 3,
                'High': 5,
                'Auto': 0
            },
            'wtw': 0
        }
    },
    '0100004795': {
        'deviceType': 'gree_8',
        'base': '[po][mo][wi][sw][tt][li]10009090000500'
    },
    '0180333331': {
        'deviceType': 'haier_1',
        'base': '[po][mo][wi][sw][tt]1'
    },
    '0180666661': {
        'deviceType': 'aux_1',
        'base': '[po][mo][wi][sw][tt]1'
    },
    '0180777771': {
        'deviceType': 'chigo_1',
        'base': '[po][mo][wi][sw][tt]1'
    }
}

class XiaomiACCompanion(AirConditioningCompanion):
    def send_configuration(self, model: str, power: Power,
                           operation_mode: OperationMode,
                           target_temperature: int, fan_speed: FanSpeed,
                           swing_mode: SwingMode, led: Led):

        prefix = str(model[0:2] + model[8:16])
        suffix = model[-1:]

        # Static turn off command available?
        if (power is Power.Off) and (prefix in DEVICE_COMMAND_TEMPLATES) and \
                (POWER_OFF in DEVICE_COMMAND_TEMPLATES[prefix]):
            return self.send_command(
                prefix + DEVICE_COMMAND_TEMPLATES[prefix][POWER_OFF])

        if prefix in DEVICE_COMMAND_TEMPLATES:
            configuration = prefix + DEVICE_COMMAND_TEMPLATES[prefix]['base']
        else:
            configuration = \
                prefix + DEVICE_COMMAND_TEMPLATES['fallback']['base']

        configuration = configuration.replace('[po]', str(power.value))
        configuration = configuration.replace('[mo]', str(operation_mode.value))
        configuration = configuration.replace('[wi]', str(fan_speed.value))
        configuration = configuration.replace('[sw]', str(swing_mode.value))
        configuration = configuration.replace('[tt]', format(target_temperature, 'X'))

        if operation_mode==OperationMode.Dehumidify:
            fan_speed = FanSpeed.Low
        if prefix in DEVICE_COMMAND_TEMPLATES:
            template = DEVICE_COMMAND_TEMPLATES[prefix]
            li = '0' if power is Power.Off else str(led.value)
            if 'extra' in template:
                extra = template['extra']                
                li += '1' if led.value=='0' else '0'
                configuration = configuration.replace('[li]', li)

                wtw = extra['wtw'] if 'wtw' in extra else 0
                if (fan_speed==FanSpeed.Medium) or (fan_speed==FanSpeed.High):
                    wtw += 3
                elif fan_speed==FanSpeed.Low:
                    wtw += 1
                if power is Power.Off:
                    wtw = 4
                configuration = configuration.replace('[wtw]', str(wtw))

                pmp_mode = operation_mode.name
                if power is Power.Off:
                    pmp_mode = 'Off'
                pmp = extra['pmp'][pmp_mode] if pmp_mode in extra['pmp'] else '00'
                configuration  = configuration.replace('[pmp]', pmp)

                for item in [{'key':'tt1', 'value':1, 'off': 0}, {'key':'tt2', 'value':4}, {'key':'tt3', 'value':7, 'off': 10}]:
                    mode = operation_mode.name
                    if power is Power.Off:
                        mode = 'Off'
                    tc = (extra[item['key']][mode] if mode in extra[item['key']] else item['value']) if item['key'] in extra else item['value']
                    if item['key']=='tt3':
                        if fan_speed.value < 3:
                            tc = tc + 1 + (fan_speed.value * 2)
                    t = format((tc + target_temperature - 17) % 16, 'X')
                    if power is Power.Off and 'off' in item:
                        t = format(item['off'], 'X')
                    if item['key']=='tt2' and power is Power.Off:
                        t = 'D'
                    configuration = configuration.replace('['+item['key']+']', t)
                    
                wbw = (extra['wbw'][fan_speed.name] if fan_speed.name in extra['wbw'] else 0) if 'wbw' in extra else 0
                if power is Power.Off:
                    wbw = 0
                configuration = configuration.replace('[wbw]', str(wbw))               

        else:
            temperature = format((1 + target_temperature - 17) % 16, 'X')
            configuration = configuration.replace('[tt1]', temperature)

            temperature = format((4 + target_temperature - 17) % 16, 'X')
            configuration = configuration.replace('[tt4]', temperature)

            temperature = format((7 + target_temperature - 17) % 16, 'X')
            configuration = configuration.replace('[tt7]', temperature)

        configuration = configuration + '0' #suffix
        _LOGGER.debug(configuration)
        if power is Power.Off:
            _LOGGER.info('*******************the air condition is power off now********************')
        _LOGGER.info('@@@@@@@@@@@@@@@@@@log power state@@@@@@@@@@@')
        _LOGGER.info(power)
        return self.send_command(configuration)


class XiaomiACCompanionV3(XiaomiACCompanion):
    def __init__(self, ip: str = None, token: str = None, start_id: int = 0,
                 debug: int = 0, lazy_discover: bool = True) -> None:
        super().__init__(ip, token, start_id, debug, lazy_discover,
                         model=MODEL_ACPARTNER_V3)

    @command(
        default_output=format_output("Powering socket on"),
    )
    def socket_on(self):
        """Socket power on."""
        return self.send("toggle_plug", ["on"])

    @command(
        default_output=format_output("Powering socket off"),
    )
    def socket_off(self):
        """Socket power off."""
        return self.send("toggle_plug", ["off"])

    @command(
        default_output=format_output(
            "",
            "Power: {result.power}\n"
            "Power socket: {result.power_socket}\n"
            "Load power: {result.load_power}\n"
            "Air Condition model: {result.air_condition_model}\n"
            "LED: {result.led}\n"
            "Target temperature: {result.target_temperature} °C\n"
            "Swing mode: {result.swing_mode}\n"
            "Fan speed: {result.fan_speed}\n"
            "Mode: {result.mode}\n"
        )
    )
    def status(self) -> AirConditioningCompanionStatus:
        """Return device status."""
        status = self.send("get_model_and_state")
        power_socket = self.send("get_device_prop", ["lumi.0", "plug_state"])
        return AirConditioningCompanionStatus(dict(
            model_and_state=status, power_socket=power_socket))
