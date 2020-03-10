import os
import sys

from acconeer.exptool import configs, recording, utils

from acconeer.exptool.clients import SocketClient, SPIClient, UARTClient


def main():
    parser = utils.ExampleArgumentParser()
    parser.add_argument("-t", "--temp",  type=str, required=True)
    parser.add_argument("-l", "--label",  type=str, required=False) # Sätt till true sedan
    parser.add_argument("-o", "--output-file", type=str, required=True)
    parser.add_argument("-lim", "--limit-frames", type=int)
    parser.add_argument("-a", "--angel", type=str, required=True)
    parser.add_argument("-d", "--distance", type=str, required=True)
    args = parser.parse_args()
    utils.config_logging(args)

    try:
        float(args.temp)
    except:
        print("Temp value not a float. Make sure you use . instead of , !")
        sys.exit(1)
        
    valid_arguments = ["snow", "wet", "ice", "dry", "metal"]
    if args.label.lower() not in valid_arguments:
        print("Not a valid label. Only", *valid_arguments, sep=", "), print("are accepted labels!")
        sys.exit(1)
    
    if os.path.exists(args.output_file):
        print("File '{}' already exists, won't overwrite".format(args.output_file))
        sys.exit(1)

    _, ext = os.path.splitext(args.output_file)
    if ext.lower() not in [".h5", ".npz"]:
        print("Unknown format '{}'".format(ext))
        sys.exit(1)

    if args.limit_frames is not None and args.limit_frames < 1:
        print("Frame limit must be at least 1") 
        sys.exit(1)

    if args.socket_addr:
        client = SocketClient(args.socket_addr)
    elif args.spi:
        client = SPIClient()
    else:
        port = args.serial_port or utils.autodetect_serial_port()
        client = UARTClient(port)

    config = configs.IQServiceConfig()
    config.sensor = args.sensors
    config.update_rate = 150 #Ändra samplingsfrekvens här
    config.range_interval = [0.15, 2] #Avståndsintervall i meter

    session_info = client.setup_session(config)
    
    recorder = recording.Recorder(sensor_config=config, session_info=session_info, temp=args.temp, label=args.label.lower(), angel=args.angel, distance=args.distance)
    client.start_session()

    interrupt_handler = utils.ExampleInterruptHandler()
    print("Press Ctrl-C to end session")

    i = 0
    while not interrupt_handler.got_signal:
        data_info, data = client.get_next()
        recorder.sample(data_info, data)

        i += 1

        if args.limit_frames:
            print("Sampled {:>4}/{}".format(i, args.limit_frames), end="\r", flush=True)

            if i >= args.limit_frames:
                break
        else:
            print("Sampled {:>4}".format(i), end="\r", flush=True)

    

    client.disconnect()

    record = recorder.close()
    recording.save(args.output_file, record)
    print("Saved to '{}'".format(args.output_file))


if __name__ == "__main__":
    main()
