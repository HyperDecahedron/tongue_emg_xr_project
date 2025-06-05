using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;
using Unity.XR.CoreUtils; 

public class UDP_Listener : MonoBehaviour
{
    public XROrigin xrOrigin; 

    UdpClient udpClient;
    Thread receiveThread;

    float moveAmount = 0.1f;

    void Start()
    {
        udpClient = new UdpClient(5052);  // Match the port in Python
        receiveThread = new Thread(new ThreadStart(ReceiveData));
        receiveThread.IsBackground = true;
        receiveThread.Start();

        // Ensure dispatcher is initialized
        UnityMainThreadDispatcher.Instance();
    }

    void ReceiveData()
    {
        IPEndPoint remoteEndPoint = new IPEndPoint(IPAddress.Any, 5052);
        while (true)
        {
            try
            {
                byte[] data = udpClient.Receive(ref remoteEndPoint);
                string gesture = Encoding.ASCII.GetString(data).Trim().ToLower();
                Debug.Log("Received gesture: " + gesture);

                if (gesture == "l" || gesture == "r" || gesture == "f")
                {
                    UnityMainThreadDispatcher.Instance().Enqueue(() => MoveXROrigin(gesture));
                }
            }
            catch (SocketException ex)
            {
                Debug.Log("Socket exception: " + ex);
            }
        }
    }

    void MoveXROrigin(string gesture)
    {
        if (xrOrigin == null) return;

        Vector3 move = Vector3.zero;

        switch (gesture)
        {
            case "l":
                move = Vector3.left * moveAmount;
                break;
            case "r":
                move = Vector3.right * moveAmount;
                break;
            case "f":
                move = Vector3.forward * moveAmount;
                break;
        }

        xrOrigin.transform.position += move;
    }

    void OnApplicationQuit()
    {
        receiveThread.Abort();
        udpClient.Close();
    }
}
